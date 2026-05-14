"""
greenmind.py — GreenMind Core Agent
=====================================
Handles classification, routing, onboarding state machine,
eco score calculation, and habit tracking.

Modes: educator | habit | prompt | none
"""

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
# Onboarding Steps (drives the guided question flow)
# -----------------------------------------------------------------

ONBOARDING_STEPS = [
    {
        "key":      "prompts_per_day",
        "question": "To understand your AI habits, about how many prompts do you send per day?",
        "buttons":  ["0–10", "10–20", "20–40", "40+"],
    },
    {
        "key":      "retries",
        "question": "How often do you regenerate or retry answers?",
        "buttons":  ["Rarely", "1–5 times", "5–10 times", "More than 10"],
    },
    {
        "key":      "main_use",
        "question": "What do you mainly use AI for?",
        "buttons":  ["Studying", "Coding", "Writing", "Research", "Mixed"],
    },
    {
        "key":      "deadline",
        "question": "Are you currently under deadline pressure?",
        "buttons":  ["Yes", "No"],
    },
]

# -----------------------------------------------------------------
# Eco Score — computes 0–100 from onboarding profile
# -----------------------------------------------------------------

def compute_eco_score(profile: dict) -> dict:
    """
    Returns score (int 0-100), breakdown (dict), and what-if simulation.
    Higher = greener.
    """
    score = 100

    # Penalty: prompts per day
    ppd = profile.get("prompts_per_day", "0–10")
    ppd_penalty = {"0–10": 0, "10–20": 8, "20–40": 18, "40+": 30}
    score -= ppd_penalty.get(ppd, 0)

    # Penalty: retries
    retries = profile.get("retries", "Rarely")
    retry_penalty = {"Rarely": 0, "1–5 times": 5, "5–10 times": 15, "More than 10": 28}
    score -= retry_penalty.get(retries, 0)

    # Penalty: main use (coding = heavier compute)
    use_penalty = {"Studying": 3, "Writing": 3, "Research": 5, "Mixed": 8, "Coding": 12}
    score -= use_penalty.get(profile.get("main_use", "Mixed"), 5)

    # Penalty: deadline pressure (rushed prompting)
    if profile.get("deadline") == "Yes":
        score -= 7

    score = max(0, min(100, score))

    # Loss factors
    factors = []
    if ppd_penalty.get(ppd, 0) > 0:
        factors.append(f"High prompt volume ({ppd}/day) −{ppd_penalty[ppd]} pts")
    if retry_penalty.get(retries, 0) >= 15:
        factors.append(f"Frequent retries ({retries}) −{retry_penalty[retries]} pts")
    if profile.get("deadline") == "Yes":
        factors.append("Deadline pressure (rushed prompting) −7 pts")

    # What-if: reduce retries to 1–5 times
    what_if_gain = 0
    current_retry_penalty = retry_penalty.get(retries, 0)
    target_retry_penalty  = retry_penalty.get("1–5 times", 5)
    if current_retry_penalty > target_retry_penalty:
        what_if_gain = current_retry_penalty - target_retry_penalty

    return {
        "score":        score,
        "loss_factors": factors,
        "what_if": {
            "action":       "Reduce retries to 1–5 times",
            "points_gained": what_if_gain,
            "new_score":    min(100, score + what_if_gain),
        },
    }


# -----------------------------------------------------------------
# Callback
# -----------------------------------------------------------------

class CustomCallback(BaseCallbackHandler):

    def __init__(self):
        self.messages = {}

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.messages["on_llm_start_prompts"] = prompts
        self.messages["on_llm_start_kwargs"]  = kwargs

    def on_llm_end(self, response: LLMResult, **kwargs):
        self.messages["on_llm_end_response"] = response
        self.messages["on_llm_end_kwargs"]   = kwargs


# -----------------------------------------------------------------
# GreenMind Agent
# -----------------------------------------------------------------

class GreenMindAgent:

    STATE_EDUCATOR = "educator"
    STATE_HABIT    = "habit"
    STATE_PROMPT   = "prompt"
    STATE_NONE     = "none"

    # ── Onboarding phases ──────────────────────────────────────
    PHASE_IDLE       = "idle"          # not yet started
    PHASE_ONBOARDING = "onboarding"    # collecting profile
    PHASE_ACTIVE     = "active"        # normal chat

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

        # Onboarding state machine
        self.onboarding_phase   = GreenMindAgent.PHASE_IDLE
        self.onboarding_step    = 0          # index into ONBOARDING_STEPS
        self.onboarding_profile = {}         # collected answers

        # Habit tracker
        self.habit_tracker = {
            "track_independent_thinking": False,
            "track_retries":              False,
            "track_prompt_quality":       False,
            "week_goal":                  "Reduce retries by 30%",
            "activated":                  False,
            "daily_log":                  [],  # list of { date, tried_first, retries }
        }

        # Load chains
        self.educator_chain = self._chain("prompts/educator_prompt.txt")
        self.habit_chain    = self._chain("prompts/habit_prompt.txt")
        self.prompt_chain   = self._chain("prompts/prompt_advisor_prompt.txt")

        self.classifier_prompt = self._load_json("prompts/classifier_prompt.json")
        self.text_classifier   = self._build_classifier()

    # ── File helpers ────────────────────────────────────────────

    def _load_txt(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _chain(self, path):
        text   = self._load_txt(path)
        prompt = PromptTemplate.from_template(text)
        return prompt | self.llm | StrOutputParser()

    # ── Classifier ──────────────────────────────────────────────

    def _build_classifier(self):
        data = self.classifier_prompt

        # Build label definitions — support both 3-label and 4-label classifier files
        label_defs = "\n".join(
            f"- {k}: {v}" for k, v in data["labels"].items()
        )

        examples_text = "\n".join(
            f"Message: {ex['message']}\nClassification: {ex['label']}"
            for ex in data["examples"]
        )

        prompt_text = f"""{data["system"]}

{data["rules"]}

Definitions:
{label_defs}

Examples:
{examples_text}

Message: {{message}}
Classification:"""

        return (
            PromptTemplate.from_template(prompt_text)
            | self.text_classifier_llm
            | StrOutputParser()
        )

    # ── Onboarding state machine ────────────────────────────────

    def start_onboarding(self):
        """Called when student clicks a starter button on first launch."""
        self.onboarding_phase = GreenMindAgent.PHASE_ONBOARDING
        self.onboarding_step  = 0
        self.onboarding_profile = {}
        return self._current_onboarding_question()

    def _current_onboarding_question(self):
        step = ONBOARDING_STEPS[self.onboarding_step]
        return {
            "type":     "onboarding",
            "message":  step["question"],
            "buttons":  step["buttons"],
            "step":     self.onboarding_step,
            "total":    len(ONBOARDING_STEPS),
        }

    def advance_onboarding(self, answer: str):
        """
        Record answer, advance step.
        Returns next question dict OR completion dict (with eco_score).
        """
        step_key = ONBOARDING_STEPS[self.onboarding_step]["key"]
        self.onboarding_profile[step_key] = answer
        self.onboarding_step += 1

        if self.onboarding_step < len(ONBOARDING_STEPS):
            return self._current_onboarding_question()

        # Onboarding complete — compute eco score
        self.onboarding_phase = GreenMindAgent.PHASE_ACTIVE
        eco = compute_eco_score(self.onboarding_profile)

        diagnosis = self._build_diagnosis()

        return {
            "type":      "onboarding_complete",
            "profile":   self.onboarding_profile,
            "diagnosis": diagnosis,
            "eco_score": eco,
            "message":   (
                f"Based on today's usage:\n\n"
                f"**Prompts/day:** {self.onboarding_profile.get('prompts_per_day')}\n"
                f"**Retries:** {self.onboarding_profile.get('retries')}\n"
                f"**Main use:** {self.onboarding_profile.get('main_use')}\n\n"
                f"Can you paste one prompt you recently used in ChatGPT? "
                f"I'll show you exactly what to improve."
            ),
        }

    def _build_diagnosis(self):
        checks = []
        use  = self.onboarding_profile.get("main_use", "")
        ret  = self.onboarding_profile.get("retries", "")
        dead = self.onboarding_profile.get("deadline", "No")

        if use:
            checks.append(f"Heavy {use.lower()} usage detected")
        if ret in ("5–10 times", "More than 10"):
            checks.append("Frequent retries detected")
        if dead == "Yes":
            checks.append("Deadline pressure — rushed prompting likely")
        return checks

    def is_onboarding_answer(self, message: str) -> bool:
        """True if the message matches a button option in the current onboarding step."""
        if self.onboarding_phase != GreenMindAgent.PHASE_ONBOARDING:
            return False
        if self.onboarding_step >= len(ONBOARDING_STEPS):
            return False
        opts = [o.lower() for o in ONBOARDING_STEPS[self.onboarding_step]["buttons"]]
        return message.strip().lower() in opts

    # ── Habit tracker ────────────────────────────────────────────

    def activate_habit_tracker(self):
        self.habit_tracker["activated"] = True
        self.habit_tracker["track_independent_thinking"] = True
        self.habit_tracker["track_retries"]              = True
        self.habit_tracker["track_prompt_quality"]       = True

    def log_habit_day(self, tried_first: bool, retries: int):
        from datetime import date
        self.habit_tracker["daily_log"].append({
            "date":        str(date.today()),
            "tried_first": tried_first,
            "retries":     retries,
        })

    def get_habit_summary(self) -> dict:
        log = self.habit_tracker["daily_log"]
        if not log:
            return {"message": "No habit data yet — check back tomorrow!"}
        avg_retries   = sum(d["retries"] for d in log) / len(log)
        tried_pct     = sum(1 for d in log if d["tried_first"]) / len(log) * 100
        return {
            "days_tracked":       len(log),
            "avg_retries":        round(avg_retries, 1),
            "tried_first_pct":    round(tried_pct, 1),
            "week_goal":          self.habit_tracker["week_goal"],
        }

    # ── Main response ────────────────────────────────────────────

    def get_response(self, user_message: str, chat_history: list):
        """
        Central dispatch. Returns (response_text, log_dict).
        Special structured returns are JSON-encoded strings prefixed
        with __STRUCTURED__: so the API can forward them to the frontend.
        """

        # 1. Onboarding phase — handle button answers
        if self.onboarding_phase == GreenMindAgent.PHASE_ONBOARDING:
            if self.is_onboarding_answer(user_message):
                result = self.advance_onboarding(user_message)
                return json.dumps({"__structured__": result}), {
                    "user_message": user_message,
                    "state": "onboarding",
                    "classification": {"result": "onboarding"},
                }

        # 2. Habit tracker — "yes" after habit tracking prompt
        if (
            self.onboarding_phase == GreenMindAgent.PHASE_ACTIVE
            and user_message.strip().lower() in ("yes", "yes please")
            and not self.habit_tracker["activated"]
        ):
            self.activate_habit_tracker()
            payload = {
                "__structured__": {
                    "type":    "habit_activated",
                    "message": (
                        "Habit tracking activated!\n\n"
                        "Tomorrow I'll track:\n"
                        "✓ Independent thinking (trying before asking AI)\n"
                        "✓ Retries\n"
                        "✓ Prompt quality\n\n"
                        f"Your goal for this week: **{self.habit_tracker['week_goal']}**"
                    ),
                    "tracking": self.habit_tracker,
                }
            }
            return json.dumps(payload), {
                "user_message": user_message,
                "state": "habit_activated",
                "classification": {"result": "habit"},
            }

        # 3. Normal classification + routing
        clf_cb = CustomCallback()
        raw = self.text_classifier.invoke(
            {"message": user_message},
            {"callbacks": [clf_cb], "stop_sequences": ["\n"]},
        )
        classification = raw.strip().lower()

        valid = {
            GreenMindAgent.STATE_EDUCATOR,
            GreenMindAgent.STATE_HABIT,
            GreenMindAgent.STATE_PROMPT,
        }
        if classification in valid:
            self.state = classification

        chain_map = {
            GreenMindAgent.STATE_EDUCATOR: self.educator_chain,
            GreenMindAgent.STATE_HABIT:    self.habit_chain,
            GreenMindAgent.STATE_PROMPT:   self.prompt_chain,
        }
        chain = chain_map.get(self.state, self.educator_chain)

        resp_cb  = CustomCallback()
        response = chain.invoke(
            {
                "user_message": user_message,
                "chat_history": "\n".join(chat_history),
            },
            {"callbacks": [resp_cb], "stop_sequences": ["\n"]},
        )

        # After a prompt coaching response, always append the habit-forming nudge
        if self.state == GreenMindAgent.STATE_PROMPT:
            response += (
                "\n\n---\n**Before you close this session:** Did you try solving "
                "this yourself before asking AI? Building that habit cuts your retry "
                "count dramatically. GreenMind can track this for you if you'd like."
            )

        return response, {
            "user_message":      user_message,
            "chatbot_response":  response,
            "state":             self.state,
            "classification":    {"result": classification},
            "classification_log": dict(clf_cb.messages),
            "response_log":      dict(resp_cb.messages),
        }


# -----------------------------------------------------------------
# Log Writer
# -----------------------------------------------------------------

class LogWriter:

    def __init__(self, filename="greenmind_conversation.jsonl"):
        self.conversation_logfile = filename
        if os.path.exists(self.conversation_logfile):
            os.remove(self.conversation_logfile)

    def make_json_safe(self, value):
        if isinstance(value, list):
            return [self.make_json_safe(x) for x in value]
        if isinstance(value, dict):
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


# -----------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------

if __name__ == "__main__":

    agent        = GreenMindAgent()
    chat_history = []
    log_writer   = LogWriter()

    print("GreenMind: Hi, I'm GreenMind 🌱")
    print("GreenMind: I help students use AI smarter, save time, and build greener habits.")
    print("GreenMind: What's happening with your AI usage today?")
    print("           [I spend too much time / I keep retrying / My prompts don't work / Check my habits]")

    while True:
        user_message = input("Student: ")
        if user_message.lower() in ("quit", "exit", "bye"):
            print("GreenMind: Good luck with your studies. Goodbye!")
            break

        chatbot_response, log = agent.get_response(user_message, chat_history)

        # Handle structured responses in CLI
        if chatbot_response.startswith('{"__structured__"'):
            data = json.loads(chatbot_response)["__structured__"]
            print(f"\nGreenMind [{data.get('type', 'system')}]:")
            print(data.get("message", ""))
            if "buttons" in data:
                print("Options:", " | ".join(data["buttons"]))
            if "eco_score" in data:
                eco = data["eco_score"]
                print(f"\n🌱 Eco Score: {eco['score']} / 100")
                for f in eco["loss_factors"]:
                    print(f"  − {f}")
        else:
            print(f"GreenMind [{agent.state}]: {chatbot_response}")

        chat_history.extend([f"Student: {user_message}", f"GreenMind: {chatbot_response}"])
        log_writer.write(log)
