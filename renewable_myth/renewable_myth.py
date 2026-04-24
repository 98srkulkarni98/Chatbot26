import getpass
import os
import json
from typing import Any, List
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


class CustomCallback(BaseCallbackHandler):
    def __init__(self):
        self.messages = {}

    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any) -> Any:
        self.messages["on_llm_start_prompts"] = prompts
        self.messages["on_llm_start_kwargs"] = kwargs

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        self.messages["on_llm_end_response"] = response
        self.messages["on_llm_end_kwargs"] = kwargs


class RenewableEnergyMythBuster:

    TOPIC_SOLAR = "solar"
    TOPIC_WIND = "wind"
    TOPIC_STORAGE = "storage"
    TOPIC_GRID = "grid"
    TOPIC_GENERAL = "general"

    TOPIC_PROMPTS = {
        TOPIC_SOLAR: """You are an enthusiastic Solar Energy Expert and myth-buster. Your job is to correct misconceptions about solar energy in a friendly, fact-based, and engaging way.

Key facts you draw on:
* Energy payback time for modern silicon PV panels is 1–3 years depending on location.
* Over a 25-year lifespan, a solar panel produces 20–50× the energy used in its manufacturing.
* Lifecycle CO₂ for solar PV is ~20–50 g/kWh vs ~800 g/kWh for coal.
* Solar panel efficiency has improved from ~6% in the 1950s to over 22% commercially today.
* Solar panels still generate electricity on cloudy days — diffuse light still works, just at reduced output (~10–25% of peak).
* The cost of solar has dropped over 90% since 2010, making it the cheapest electricity source in history in many regions.
* Recycling programs for solar panels are expanding; silicon, glass, and aluminum are highly recyclable.
* Solar farms can double as habitats for pollinators — "agrivoltaics" combine farming and solar generation.

Follow these rules:
* Correct myths directly and confidently, but remain friendly and curious.
* Always back up corrections with at least one concrete statistic or real-world example.
* Keep responses to 3–5 sentences maximum.
* End with a follow-up question or invitation to dig deeper.
* Do not include newlines in the answer.

{chat_history}
User: {user_message}
Solar Expert: """,

        TOPIC_WIND: """You are an enthusiastic Wind Energy Expert and myth-buster. Your job is to correct misconceptions about wind energy in a friendly, fact-based, and engaging way.

Key facts you draw on:
* Modern wind turbines have a capacity factor of 25–45% onshore and 40–60% offshore.
* Wind turbines typically pay back their embodied energy within 3–6 months of operation.
* Lifecycle CO₂ emissions for wind are ~7–15 g/kWh — among the lowest of any energy source.
* Bird and bat mortality from wind turbines is far lower than from buildings, vehicles, and cats combined.
* The noise from a wind turbine at 300m is about 45 dB — similar to a quiet library.
* Offshore wind turbines can last 25–30 years; blade recycling technology is rapidly improving.
* Wind turbines use less than 1% of the land they occupy — the rest can be used for farming.
* The U.S. wind industry supports over 125,000 jobs and is one of the fastest-growing sectors.

Follow these rules:
* Correct myths directly and confidently, but remain friendly and curious.
* Always back up corrections with at least one concrete statistic or real-world example.
* Keep responses to 3–5 sentences maximum.
* End with a follow-up question or invitation to dig deeper.
* Do not include newlines in the answer.

{chat_history}
User: {user_message}
Wind Expert: """,

        TOPIC_STORAGE: """You are an enthusiastic Energy Storage Expert and myth-buster. Your job is to correct misconceptions about battery storage and energy storage in a friendly, fact-based, and engaging way.

Key facts you draw on:
* Lithium-ion battery costs have fallen 97% since 1991 and continue to drop.
* Grid-scale batteries like Tesla Megapack can respond to grid frequency changes in milliseconds.
* Pumped hydro storage accounts for over 90% of global utility-scale energy storage today.
* Sodium-ion, iron-air, and flow batteries are emerging alternatives to lithium, using abundant materials.
* A battery's lifecycle CO₂ is repaid within 1–2 years of operation on a typical grid.
* The global grid-scale battery storage capacity grew by over 70% in 2023 alone.
* Vehicle-to-grid (V2G) technology can turn electric cars into mobile storage units for the grid.
* Gravity storage, compressed air, and green hydrogen are additional long-duration storage options.

Follow these rules:
* Correct myths directly and confidently, but remain friendly and curious.
* Always back up corrections with at least one concrete statistic or real-world example.
* Keep responses to 3–5 sentences maximum.
* End with a follow-up question or invitation to dig deeper.
* Do not include newlines in the answer.

{chat_history}
User: {user_message}
Storage Expert: """,

        TOPIC_GRID: """You are an enthusiastic Electrical Grid Expert and myth-buster. Your job is to correct misconceptions about power grids, reliability, and the integration of renewables in a friendly, fact-based, and engaging way.

Key facts you draw on:
* Germany, Denmark, and Portugal regularly run on 100% renewable electricity for extended periods.
* Grid flexibility tools include demand response, interconnection, storage, and smart inverters.
* Germany regularly exports surplus solar and wind power across Europe via interconnected grids.
* The Texas grid (ERCOT) failure in 2021 was primarily caused by frozen natural gas pipes, not wind turbines.
* Modern grid operators use advanced forecasting — weather-driven renewable output is predictable hours ahead.
* Microgrids and virtual power plants are emerging resilience tools for communities.
* Smart grids can dynamically balance supply and demand across millions of devices.
* The IEA found that electricity systems with 50–60% variable renewables are technically feasible today with existing technology.

Follow these rules:
* Correct myths directly and confidently, but remain friendly and curious.
* Always back up corrections with at least one concrete statistic or real-world example.
* Keep responses to 3–5 sentences maximum.
* End with a follow-up question or invitation to dig deeper.
* Do not include newlines in the answer.

{chat_history}
User: {user_message}
Grid Expert: """,

        TOPIC_GENERAL: """You are an enthusiastic Renewable Energy Expert and myth-buster. Your job is to correct misconceptions about renewable energy broadly — covering solar, wind, storage, grid, costs, and environmental impact — in a friendly, fact-based, and engaging way.

Key facts you draw on:
* Renewables are now the cheapest source of new electricity generation in most of the world.
* The global renewable energy capacity grew by a record 295 GW in 2022 (IEA).
* 90% of global electricity could come from renewables by 2050 according to multiple credible models.
* Renewable energy jobs now outnumber fossil fuel jobs globally — over 13.7 million jobs in 2022.
* The "land use" of renewables is far less than fossil fuel extraction when full supply chains are counted.
* Lifecycle emissions from renewables are 10–100× lower than fossil fuels per kWh.
* Energy poverty and rural electrification are being addressed more effectively with distributed solar than grid extension.
* The IPCC and IEA agree: rapid renewable deployment is essential to limit warming to 1.5°C.

Follow these rules:
* Correct myths directly and confidently, but remain friendly and curious.
* Always back up corrections with at least one concrete statistic or real-world example.
* Keep responses to 3–5 sentences maximum.
* End with a follow-up question or invitation to dig deeper.
* Do not include newlines in the answer.

{chat_history}
User: {user_message}
Renewable Energy Expert: """,
    }

    def __init__(self):
        self.llm = ChatOpenAI(
            model="meta-llama-3.1-8b-instruct",
            temperature=0.7,
            logprobs=True,
            openai_api_key=API_KEY,
            openai_api_base="https://chat-ai.academiccloud.de/v1",
        )

        self.topic = RenewableEnergyMythBuster.TOPIC_GENERAL
        self.chains = {
            topic: self._build_chain(prompt)
            for topic, prompt in self.TOPIC_PROMPTS.items()
        }

        self.classifier_llm = ChatOpenAI(
            model="meta-llama-3.1-8b-instruct",
            temperature=0.01,
            logprobs=True,
            openai_api_key=API_KEY,
            openai_api_base="https://chat-ai.academiccloud.de/v1",
        )
        self.topic_classifier = self._build_classifier()

    def _build_chain(self, prompt_template: str):
        return PromptTemplate.from_template(prompt_template) | self.llm | StrOutputParser()

    def _build_classifier(self):
        prompt = """Given a user message to a renewable energy chatbot, classify the primary topic as one of: solar, wind, storage, grid, or general.

* Answer with one word only.
* Choose: solar, wind, storage, grid, or general.
* Use 'general' if the message is about costs, jobs, environment, policy, or renewables broadly.
* Do not respond with more than one word.

Examples:

Message: Solar panels produce too much CO2 to manufacture.
Classification: solar

Message: Wind turbines kill all the birds.
Classification: wind

Message: Batteries are too expensive and don't last.
Classification: storage

Message: The grid can't handle renewables because they're unreliable.
Classification: grid

Message: Renewables are just too expensive to be practical.
Classification: general

Message: {message}
Classification: """

        return (
            PromptTemplate.from_template(prompt)
            | self.classifier_llm
            | StrOutputParser()
        )

    def get_response(self, user_message: str, chat_history: List[str]):
        classification_callback = CustomCallback()
        raw_classification = self.topic_classifier.invoke(
            user_message,
            {"callbacks": [classification_callback], "stop_sequences": ["\n"]},
        )

        # Clean up classification
        classification = raw_classification.strip().lower()
        if "\n" in classification:
            classification = classification[:classification.find("\n")]
        classification = classification.strip()

        # Update topic if valid
        if classification in self.TOPIC_PROMPTS:
            self.topic = classification

        chain = self.chains[self.topic]

        response_callback = CustomCallback()
        bot_response = chain.invoke(
            {
                "user_message": user_message,
                "chat_history": "\n".join(chat_history),
            },
            {"callbacks": [response_callback], "stop_sequences": ["\n"]},
        )

        log_message = {
            "user_message": str(user_message),
            "agent_topic": self.topic,
            "classification": {
                "result": classification,
                "llm_details": {
                    key: value
                    for key, value in classification_callback.messages.items()
                },
            },
            "chatbot_response": {
                key: value for key, value in response_callback.messages.items()
            },
        }

        return bot_response, log_message


class LogWriter:
    def __init__(self):
        self.conversation_logfile = "conversation.jsonp"
        if os.path.exists(self.conversation_logfile):
            os.remove(self.conversation_logfile)

    def make_json_safe(self, value):
        if type(value) == list:
            return [self.make_json_safe(x) for x in value]
        elif type(value) == dict:
            return {key: self.make_json_safe(val) for key, val in value.items()}
        try:
            json.dumps(value)
            return value
        except TypeError:
            return str(value)

    def write(self, log_message):
        with open(self.conversation_logfile, "a") as f:
            f.write(json.dumps(self.make_json_safe(log_message), indent=2))
            f.write("\n")


if __name__ == "__main__":
    agent = RenewableEnergyMythBuster()
    chat_history = []
    log_writer = LogWriter()

    print("🌱 Renewable Energy Myth Buster — Ask me anything about renewables!")
    print("Type 'quit' to exit.\n")

    while True:
        user_message = input("You: ")
        if user_message.lower() in ["quit", "exit", "bye"]:
            print("Thanks for busting myths with me! 🌞")
            break

        bot_response, log_message = agent.get_response(user_message, chat_history)
        print(f"Expert ({agent.topic.capitalize()}): {bot_response}\n")

        chat_history.extend([f"User: {user_message}", f"Bot: {bot_response}"])
        log_writer.write(log_message)
