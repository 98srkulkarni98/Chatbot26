import getpass
import os
import json
from typing import Any
from langchain_core.output_parsers import StrOutputParser
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain_core.outputs import LLMResult
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

import sys

if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
)

API_KEY = os.getenv("CHAT_AI_ACCESS_KEY")
if not API_KEY:
    API_KEY = getpass.getpass("Enter your CHAT_AI_ACCESS_KEY: ")


# -----------------------------------------------------------------
# Callback — mirrors animalbot.py exactly
# -----------------------------------------------------------------

class CustomCallback(BaseCallbackHandler):

    def __init__(self):
        self.messages = {}

    def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any
    ) -> Any:
        self.messages["on_llm_start_prompts"] = prompts
        self.messages["on_llm_start_kwargs"] = kwargs

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        self.messages["on_llm_end_response"] = response
        self.messages["on_llm_end_kwargs"] = kwargs


# -----------------------------------------------------------------
# GreenMind Agent
# -----------------------------------------------------------------

# class GreenMindAgent:

#     STATE_EDUCATOR   = "educator"
#     STATE_CALCULATOR = "calculator"
#     STATE_HABIT      = "habit"
#     STATE_COMPANY    = "company"
#     STATE_POLICY     = "policy"

#     def __init__(self):

#         self.llm = ChatOpenAI(
#             model="meta-llama-3.1-8b-instruct",
#             temperature=0.6,
#             logprobs=True,
#             openai_api_key=API_KEY,
#             openai_api_base="https://chat-ai.academiccloud.de/v1",
#         )

#         self.text_classifier_llm = ChatOpenAI(
#             model="meta-llama-3.1-8b-instruct",
#             temperature=0.01,
#             logprobs=True,
#             openai_api_key=API_KEY,
#             openai_api_base="https://chat-ai.academiccloud.de/v1",
#         )

#         self.state = GreenMindAgent.STATE_EDUCATOR

#         self.educator_chain   = self.create_educator_chain()
#         self.calculator_chain = self.create_calculator_chain()
#         self.habit_chain      = self.create_habit_chain()
#         self.company_chain    = self.create_company_chain()
#         self.policy_chain     = self.create_policy_chain()
#         self.text_classifier  = self.create_text_classifier()

#     # -- Chains ----------------------------------------------------

#     def create_educator_chain(self):
#         prompt = """You are GreenMind, an AI assistant that educates users about the hidden environmental costs of AI and large language models.

# Your knowledge covers:
# * Energy consumption per query - LLMs use roughly 10x more energy than a Google search
# * CO2 emissions from training large models (GPT-4 training emitted ~500 tonnes of CO2)
# * Water usage - data centers used ~700 million litres per day in 2023 for cooling
# * E-waste from hardware refresh cycles in data centers
# * Geographic variation in grid carbon intensity
# * Relatable comparisons: flights, car trips, household appliances

# Follow these rules:
# * Give factual, concrete responses with approximate figures where relevant.
# * Use relatable analogies to make large numbers feel tangible.
# * Keep responses to 3-5 sentences.
# * Never be preachy or guilt-trip the user.
# * Do not include any newlines in the answer.
# * You must NEVER call tools or functions.
# * You must NEVER output text like tool_call(...).
# * Always answer in plain natural language.

# {chat_history}
# User: {user_message}
# GreenMind: """
#         return PromptTemplate.from_template(prompt) | self.llm | StrOutputParser()

#     def create_calculator_chain(self):
#         prompt = """You are GreenMind, an AI carbon and water footprint calculator for AI usage.

# When given usage details, calculate and present:
# * Estimated weekly / monthly / annual energy use in kWh
# * CO2 equivalent in kg - use 0.41 kg CO2 per kWh as average grid intensity
# * Water usage in litres - use 1.8 litres per kWh for data center cooling
# * A relatable comparison such as car kilometres driven or plastic bottles

# Use these assumptions if the user does not specify:
# * Simple text query = 0.001 kWh
# * Image generation = 0.01 kWh
# * 1-hour coding session with AI = 0.05 kWh
# * Video generation = 0.1 kWh

# Follow these rules:
# * Always show your calculation steps clearly.
# * If the user has not given enough detail, ask one clarifying question.
# * Round all numbers to 2 decimal places.
# * End with one personalised sustainability suggestion.
# * Do not include any newlines in the answer.
# * You must NEVER call tools or functions.
# * You must NEVER output text like tool_call(...).
# * Always answer in plain natural language.

# {chat_history}
# User: {user_message}
# GreenMind: """
#         return PromptTemplate.from_template(prompt) | self.llm | StrOutputParser()

#     def create_habit_chain(self):
#         prompt = """You are GreenMind, a sustainable AI habits coach.

# Your advice covers:
# * Writing better prompts to reduce the number of queries needed
# * Choosing smaller or more efficient models for simple tasks
# * Batching requests instead of iterative back-and-forth conversations
# * Scheduling heavy AI tasks during low-carbon grid windows such as at night
# * Disabling background AI features and browser copilots when not in use
# * Preferring cached or RAG-based systems over repeated generation
# * Local AI tools that run on-device such as Ollama or LM Studio

# Follow these rules:
# * Give specific, actionable advice - no vague suggestions.
# * Tailor suggestions to the user's described workflow.
# * Keep responses concise: a short paragraph or up to 5 tips.
# * Be encouraging, not guilt-inducing.
# * Do not include any newlines in the answer.
# * You must NEVER call tools or functions.
# * You must NEVER output text like tool_call(...).
# * Always answer in plain natural language.

# {chat_history}
# User: {user_message}
# GreenMind: """
#         return PromptTemplate.from_template(prompt) | self.llm | StrOutputParser()

#     def create_company_chain(self):
#         prompt = """You are GreenMind, a green AI consultant for companies and software developers.

# Your expertise includes:
# * Model selection and right-sizing - avoid defaulting to the largest model
# * Inference optimisation: quantisation, distillation, pruning
# * Response caching and RAG to eliminate redundant generation
# * Green cloud region selection: AWS us-west-2, GCP europe-west1, Azure Sweden Central
# * Carbon-aware scheduling of batch ML workloads
# * Monitoring tools: CodeCarbon, ML CO2 Impact, Carbontracker
# * Sustainable MLOps practices and green CI/CD pipelines
# * Reporting frameworks: GHG Protocol Scope 3, SBTi for tech companies

# Follow these rules:
# * Give developer-friendly, technically precise advice.
# * Reference real tools, cloud regions, and frameworks by name.
# * Structure advice as prioritised action steps.
# * Acknowledge trade-offs between performance and sustainability.
# * Do not include any newlines in the answer.
# * You must NEVER call tools or functions.
# * You must NEVER output text like tool_call(...).
# * Always answer in plain natural language.

# {chat_history}
# User: {user_message}
# GreenMind: """
#         return PromptTemplate.from_template(prompt) | self.llm | StrOutputParser()

#     def create_policy_chain(self):
#         prompt = """You are GreenMind, a policy advisor on sustainable AI infrastructure and regulation.

# Your domain covers:
# * Mandatory energy and water disclosure for AI model training and inference
# * Green procurement standards for government AI contracts
# * R&D incentives tied to model efficiency benchmarks such as performance-per-watt
# * Data center siting regulations requiring proximity to renewable energy sources
# * Water stress assessments before data center permits are issued
# * Open efficiency leaderboards similar to MLPerf but focused on carbon
# * Nuclear and grid investment strategy for AI energy demand
# * International AI sustainability standards and gaps in the EU AI Act
# * Carbon pricing mechanisms applied to compute-intensive AI workloads

# Follow these rules:
# * Be balanced - acknowledge economic and innovation trade-offs.
# * Reference real policies, acts, and initiatives where applicable.
# * Distinguish between short-term wins and long-term structural changes.
# * Tailor advice to the actor mentioned: government, regulator, NGO, or tech company.
# * Do not include any newlines in the answer.
# * You must NEVER call tools or functions.
# * You must NEVER output text like tool_call(...).
# * Always answer in plain natural language.

# {chat_history}
# User: {user_message}
# GreenMind: """
#         return PromptTemplate.from_template(prompt) | self.llm | StrOutputParser()

#     def create_text_classifier(self):
#         prompt = """Given a message to a chatbot, classify which GreenMind mode it belongs to.

# * Answer with one word only.
# * Answer with: educator, calculator, habit, company, policy, or none.
# * Do not respond with more than one word.

# Definitions:
# educator   = user wants to learn about AI environmental impact
# calculator = user wants to estimate their AI carbon or water footprint
# habit      = user wants personal tips to use AI more sustainably
# company    = user is a developer or company asking about greener AI practices
# policy     = user is asking about regulation, government, or infrastructure
# none       = the message does not clearly belong to any of the above

# Examples:

# Message: How much CO2 does training GPT-4 produce?
# Classification: educator

# Message: I use Claude 3 hours a day, what is my carbon footprint?
# Classification: calculator

# Message: How can I write better prompts to save energy?
# Classification: habit

# Message: We are building an AI product, how do we reduce our emissions?
# Classification: company

# Message: Should AI data centers pay carbon taxes?
# Classification: policy

# Message: Hello, how are you?
# Classification: none

# Message: {message}
# Classification: """
#         return (
#             PromptTemplate.from_template(prompt)
#             | self.text_classifier_llm
#             | StrOutputParser()
#         )

#     # -- Response --------------------------------------------------

#     def get_response(self, user_message, chat_history):

#         # 1. Classify intent
#         classification_callback = CustomCallback()
#         text_classification = self.text_classifier.invoke(
#             user_message,
#             {"callbacks": [classification_callback], "stop_sequences": ["\n"]},
#         )

#         if text_classification.find("\n") > 0:
#             text_classification = text_classification[0: text_classification.find("\n")]
#         text_classification = text_classification.strip().lower()

#         # 2. Switch state if a valid mode was detected
#         valid_states = {
#             GreenMindAgent.STATE_EDUCATOR,
#             GreenMindAgent.STATE_CALCULATOR,
#             GreenMindAgent.STATE_HABIT,
#             GreenMindAgent.STATE_COMPANY,
#             GreenMindAgent.STATE_POLICY,
#         }
#         if text_classification in valid_states:
#             self.state = text_classification

#         # 3. Pick the right chain
#         chain_map = {
#             GreenMindAgent.STATE_EDUCATOR:   self.educator_chain,
#             GreenMindAgent.STATE_CALCULATOR: self.calculator_chain,
#             GreenMindAgent.STATE_HABIT:      self.habit_chain,
#             GreenMindAgent.STATE_COMPANY:    self.company_chain,
#             GreenMindAgent.STATE_POLICY:     self.policy_chain,
#         }
#         chain = chain_map[self.state]

#         # 4. Generate response
#         response_callback = CustomCallback()
#         chatbot_response = chain.invoke(
#             {"user_message": user_message, "chat_history": "\n".join(chat_history)},
#             {"callbacks": [response_callback], "stop_sequences": ["\n"]},
#         )

#         # 5. Build log - mirrors animalbot.py structure
#         log_message = {
#             "user_message":     str(user_message),
#             "chatbot_response": str(chatbot_response),
#             "agent_state":      self.state,
#             "classification": {
#                 "result":      text_classification,
#                 "llm_details": {
#                     key: value
#                     for key, value in classification_callback.messages.items()
#                 },
#             },
#             "response_details": {
#                 key: value
#                 for key, value in response_callback.messages.items()
#             },
#         }

#         return chatbot_response, log_message

class GreenMindAgent:

    STATE_EDUCATOR   = "educator"
    STATE_CALCULATOR = "calculator"
    STATE_HABIT      = "habit"

    def __init__(self):

        self.llm = ChatOpenAI(
            model="meta-llama-3.1-8b-instruct",
            temperature=0.6,
            logprobs=True,
            openai_api_key=API_KEY,
            openai_api_base="https://chat-ai.academiccloud.de/v1",
            model_kwargs={"tool_choice": "none"},   # 🔥 prevents tool_call bug
        )

        self.text_classifier_llm = ChatOpenAI(
            model="meta-llama-3.1-8b-instruct",
            temperature=0.01,
            logprobs=True,
            openai_api_key=API_KEY,
            openai_api_base="https://chat-ai.academiccloud.de/v1",
            model_kwargs={"tool_choice": "none"},
        )

        self.state = GreenMindAgent.STATE_EDUCATOR

        self.educator_chain   = self.create_educator_chain()
        self.calculator_chain = self.create_calculator_chain()
        self.habit_chain      = self.create_habit_chain()

        self.text_classifier  = self.create_text_classifier()

    # ------------------------------------------------------------
    # CHAINS (unchanged – keep your prompts as-is)
    # ------------------------------------------------------------

    def create_educator_chain(self):
        prompt = """You are GreenMind, an AI assistant that educates users about the hidden environmental costs of AI and large language models.

Your knowledge covers:
* Energy consumption per query - LLMs use roughly 10x more energy than a Google search
* CO2 emissions from training large models (GPT-4 training emitted ~500 tonnes of CO2)
* Water usage - data centers used ~700 million litres per day in 2023 for cooling
* E-waste from hardware refresh cycles in data centers
* Geographic variation in grid carbon intensity
* Relatable comparisons: flights, car trips, household appliances

Follow these rules:
* Give factual, concrete responses with approximate figures where relevant.
* Use relatable analogies to make large numbers feel tangible.
* Keep responses to 3-5 sentences.
* Never be preachy or guilt-trip the user.
* Do not include any newlines in the answer.
* You must NEVER call tools or functions.
* You must NEVER output text like tool_call(...).
* Always answer in plain natural language.

{chat_history}
User: {user_message}
GreenMind: """
        return PromptTemplate.from_template(prompt) | self.llm | StrOutputParser()

    def create_calculator_chain(self):
        prompt = """You are GreenMind, an AI carbon and water footprint calculator for AI usage.

When given usage details, calculate and present:
* Estimated weekly / monthly / annual energy use in kWh
* CO2 equivalent in kg - use 0.41 kg CO2 per kWh as average grid intensity
* Water usage in litres - use 1.8 litres per kWh for data center cooling
* A relatable comparison such as car kilometres driven or plastic bottles

Use these assumptions if the user does not specify:
* Simple text query = 0.001 kWh
* Image generation = 0.01 kWh
* 1-hour coding session with AI = 0.05 kWh
* Video generation = 0.1 kWh

Follow these rules:
* Always show your calculation steps clearly.
* If the user has not given enough detail, ask one clarifying question.
* Round all numbers to 2 decimal places.
* End with one personalised sustainability suggestion.
* Do not include any newlines in the answer.
* You must NEVER call tools or functions.
* You must NEVER output text like tool_call(...).
* Always answer in plain natural language.

{chat_history}
User: {user_message}
GreenMind: """
        return PromptTemplate.from_template(prompt) | self.llm | StrOutputParser()

    def create_habit_chain(self):
        prompt = """You are GreenMind, an AI assistant that helps users develop more sustainable habits around AI usage.

Your knowledge covers:
* Energy-saving tips for AI interactions
* Water conservation strategies in data centers
* E-waste reduction methods for tech users
* Geographic considerations for grid carbon intensity

Follow these rules:
* Give actionable, concrete advice.
* Use relatable examples and analogies.
* Keep responses to 3-5 sentences.
* Never be preachy or guilt-trip the user.
* Do not include any newlines in the answer.
* You must NEVER call tools or functions.
* You must NEVER output text like tool_call(...).
* Always answer in plain natural language.

{chat_history}
User: {user_message}
GreenMind: """
        return PromptTemplate.from_template(prompt) | self.llm | StrOutputParser()

    # ------------------------------------------------------------
    # FIXED CLASSIFIER (removed company + policy)
    # ------------------------------------------------------------

    def create_text_classifier(self):
        prompt = """Given a message to a chatbot, classify which GreenMind mode it belongs to.

* Answer with one word only.
* Answer with: educator, calculator, habit, or none.
* Do not respond with more than one word.

Definitions:
educator   = user wants to learn about AI environmental impact
calculator = user wants to estimate their AI carbon or water footprint
habit      = user wants personal tips to use AI more sustainably
none       = the message does not clearly belong to any of the above

Examples:

Message: How much CO2 does training GPT-4 produce?
Classification: educator

Message: I use Claude 3 hours a day, what is my carbon footprint?
Classification: calculator

Message: How can I write better prompts to save energy?
Classification: habit

Message: Hello, how are you?
Classification: none

Message: {message}
Classification: """
        return (
            PromptTemplate.from_template(prompt)
            | self.text_classifier_llm
            | StrOutputParser()
        )

    # ------------------------------------------------------------
    # RESPONSE (cleaned)
    # ------------------------------------------------------------

    def get_response(self, user_message, chat_history):

        # 1. Classify
        classification_callback = CustomCallback()
        text_classification = self.text_classifier.invoke(
            user_message,
            {"callbacks": [classification_callback], "stop_sequences": ["\n"]},
        )

        if "\n" in text_classification:
            text_classification = text_classification.split("\n")[0]

        text_classification = text_classification.strip().lower()

        # 2. Valid states (UPDATED)
        valid_states = {
            GreenMindAgent.STATE_EDUCATOR,
            GreenMindAgent.STATE_CALCULATOR,
            GreenMindAgent.STATE_HABIT,
        }

        if text_classification in valid_states:
            self.state = text_classification

        # 3. Chain map (UPDATED)
        chain_map = {
            GreenMindAgent.STATE_EDUCATOR:   self.educator_chain,
            GreenMindAgent.STATE_CALCULATOR: self.calculator_chain,
            GreenMindAgent.STATE_HABIT:      self.habit_chain,
        }

        chain = chain_map[self.state]

        # 4. Generate response
        response_callback = CustomCallback()
        chatbot_response = chain.invoke(
            {
                "user_message": user_message,
                "chat_history": "\n".join(chat_history),
            },
            {"callbacks": [response_callback], "stop_sequences": ["\n"]},
        )

        # 5. Log
        log_message = {
            "user_message": str(user_message),
            "chatbot_response": str(chatbot_response),
            "agent_state": self.state,
            "classification": {
                "result": text_classification,
                "llm_details": dict(classification_callback.messages),
            },
            "response_details": dict(response_callback.messages),
        }

        return chatbot_response, log_message


# -----------------------------------------------------------------
# Log Writer — mirrors animalbot.py exactly
# -----------------------------------------------------------------

class LogWriter:

    def __init__(self, filename="greenmind_conversation.jsonp"):
        self.conversation_logfile = filename
        if os.path.exists(self.conversation_logfile):
            os.remove(self.conversation_logfile)

    def make_json_safe(self, value):
        if type(value) == list:
            return [self.make_json_safe(x) for x in value]
        elif type(value) == dict:
            return {key: self.make_json_safe(value) for key, value in value.items()}
        try:
            json.dumps(value)
            return value
        except TypeError:
            return str(value)

    def write(self, log_message):
        with open(self.conversation_logfile, "a") as f:
            f.write(json.dumps(self.make_json_safe(log_message), indent=2))
            f.write("\n")
            f.close()


# -----------------------------------------------------------------
# CLI entry point — mirrors animalbot.py exactly
# -----------------------------------------------------------------

if __name__ == "__main__":

    agent        = GreenMindAgent()
    chat_history = []
    log_writer   = LogWriter()

    while True:
        user_message = input("User: ")
        if user_message.lower() in ["quit", "exit", "bye"]:
            print("GreenMind: Thanks for caring about the planet. Goodbye!")
            break

        chatbot_response, log_message = agent.get_response(user_message, chat_history)
        print("GreenMind [" + agent.state + "]: " + chatbot_response)

        chat_history.extend(["User: " + user_message])
        chat_history.extend(["GreenMind: " + chatbot_response])

        log_writer.write(log_message)