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

class GreenMindAgent:

    STATE_EDUCATOR = "educator"
    STATE_CALCULATOR = "calculator"   # kept for compatibility
    STATE_HABIT = "habit"

    # ------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------

    def __init__(self):

        self.llm = ChatOpenAI(
            model="meta-llama-3.1-8b-instruct",
            temperature=0.6,
            logprobs=True,
            openai_api_key=API_KEY,
            openai_api_base="https://chat-ai.academiccloud.de/v1",
            model_kwargs={"tool_choice": "none"},
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

        # Load prompts from files
        self.educator_chain = self.create_chain_from_txt("prompts/educator_prompt.txt")
        self.habit_chain    = self.create_chain_from_txt("prompts/habit_prompt.txt")

        self.classifier_prompt = self.load_classifier_prompt("prompts/classifier_prompt.json")
        self.text_classifier   = self.create_text_classifier()

    # ------------------------------------------------------------
    # FILE LOADERS
    # ------------------------------------------------------------

    def load_txt(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def load_classifier_prompt(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------
    # CHAIN FACTORY (TXT BASED)
    # ------------------------------------------------------------

    def create_chain_from_txt(self, path):
        prompt_text = self.load_txt(path)
        prompt = PromptTemplate.from_template(prompt_text)
        return prompt | self.llm | StrOutputParser()

    # ------------------------------------------------------------
    # CLASSIFIER (JSON-DRIVEN PROMPT)
    # ------------------------------------------------------------

    def create_text_classifier(self):

        data = self.classifier_prompt

        examples_text = "\n".join([
            f"Message: {ex['message']}\nClassification: {ex['label']}"
            for ex in data["examples"]
        ])

        prompt = f"""
{data["system"]}

{data["rules"]}

Definitions:
- educator: {data["labels"]["educator"]}
- habit: {data["labels"]["habit"]}
- none: {data["labels"]["none"]}

Examples:
{examples_text}

Message: {{message}}
Classification:
"""

        return (
            PromptTemplate.from_template(prompt)
            | self.text_classifier_llm
            | StrOutputParser()
        )

    # ------------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------------

    def get_response(self, user_message, chat_history):

        classification_callback = CustomCallback()

        text_classification = self.text_classifier.invoke(
            {"message": user_message},
            {"callbacks": [classification_callback], "stop_sequences": ["\n"]},
        )

        text_classification = text_classification.strip().lower()

        valid_states = {
            GreenMindAgent.STATE_EDUCATOR,
            GreenMindAgent.STATE_HABIT,
        }

        if text_classification in valid_states:
            self.state = text_classification

        print("state:", self.state)
        print("classification:", text_classification)

        chain_map = {
            GreenMindAgent.STATE_EDUCATOR: self.educator_chain,
            GreenMindAgent.STATE_HABIT: self.habit_chain,
        }

        chain = chain_map[self.state]

        response_callback = CustomCallback()

        chatbot_response = chain.invoke(
            {
                "user_message": user_message,
                "chat_history": "\n".join(chat_history),
            },
            {"callbacks": [response_callback], "stop_sequences": ["\n"]},
        )

        return chatbot_response, {
            "user_message": user_message,
            "chatbot_response": chatbot_response,
            "state": self.state,
            "classification": {"result": text_classification},
            "classification_log": dict(classification_callback.messages),
            "response_log": dict(response_callback.messages),
        }

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
            return {k: self.make_json_safe(v) for k, v in value.items()}
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