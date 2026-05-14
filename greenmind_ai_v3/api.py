"""
api.py — GreenMind REST API v2.0
==================================
FastAPI server — now supports the full guided onboarding flow,
eco score, habit tracker, and prompt advisor mode.

Endpoints:
  POST /chat                 — send a message, get a response
  POST /onboard/start        — begin onboarding (triggered by starter button click)
  POST /onboard/answer       — submit an onboarding button answer
  GET  /eco_score/{id}       — get current eco score for a session
  POST /habit/activate       — activate habit tracker for a session
  POST /habit/log            — log a daily habit check-in
  GET  /habit/summary/{id}   — get habit tracker summary
  POST /reset                — reset chat history for a session
  GET  /state/{id}           — current agent state
  GET  /health               — health check
  GET  /modes                — available modes

Run:
  uvicorn api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import json

from greenmind import GreenMindAgent, LogWriter, compute_eco_score

# -----------------------------------------------------------------
# App setup
# -----------------------------------------------------------------

app = FastAPI(
    title="GreenMind API",
    description="Sustainable AI coach for students — prompt advisor, habits, eco score",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------
# In-memory session store
# -----------------------------------------------------------------

sessions: dict[str, dict] = {}


def get_or_create_session(session_id: str) -> dict:
    if session_id not in sessions:
        sessions[session_id] = {
            "agent":   GreenMindAgent(),
            "history": [],
            "log":     LogWriter(f"log_{session_id}.jsonl"),
        }
    return sessions[session_id]


# -----------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id:     str
    response:       str
    active_mode:    str
    classification: str
    structured:     Optional[dict] = None   # populated for onboarding / eco / habit events


class OnboardStartRequest(BaseModel):
    session_id: Optional[str] = None


class OnboardAnswerRequest(BaseModel):
    session_id: str
    answer:     str


class OnboardResponse(BaseModel):
    session_id: str
    type:       str          # "onboarding" | "onboarding_complete"
    message:    str
    buttons:    Optional[list[str]] = None
    step:       Optional[int]       = None
    total:      Optional[int]       = None
    eco_score:  Optional[dict]      = None
    diagnosis:  Optional[list[str]] = None
    profile:    Optional[dict]      = None


class HabitActivateRequest(BaseModel):
    session_id: str


class HabitLogRequest(BaseModel):
    session_id:  str
    tried_first: bool
    retries:     int


class HabitSummaryResponse(BaseModel):
    session_id:      str
    days_tracked:    int
    avg_retries:     float
    tried_first_pct: float
    week_goal:       str


class ResetRequest(BaseModel):
    session_id: str


class ResetResponse(BaseModel):
    session_id: str
    message:    str


class StateResponse(BaseModel):
    session_id:       str
    active_mode:      str
    history_length:   int
    onboarding_phase: str
    habit_activated:  bool


class HealthResponse(BaseModel):
    status:          str
    active_sessions: int


# -----------------------------------------------------------------
# Constants
# -----------------------------------------------------------------

VALID_MODES = {"educator", "habit", "prompt", "none"}


# -----------------------------------------------------------------
# Endpoints — System
# -----------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return HealthResponse(status="ok", active_sessions=len(sessions))


@app.get("/modes", tags=["System"])
def get_modes():
    return {"modes": ["educator", "habit", "prompt"]}


# -----------------------------------------------------------------
# Endpoints — Onboarding
# -----------------------------------------------------------------

@app.post("/onboard/start", response_model=OnboardResponse, tags=["Onboarding"])
def onboard_start(req: OnboardStartRequest):
    """
    Called when the student clicks a starter button on first launch.
    Initialises the session and returns the first onboarding question.
    """
    session_id = req.session_id or str(uuid.uuid4())
    session    = get_or_create_session(session_id)
    agent: GreenMindAgent = session["agent"]

    result = agent.start_onboarding()

    return OnboardResponse(
        session_id = session_id,
        type       = result["type"],
        message    = result["message"],
        buttons    = result.get("buttons"),
        step       = result.get("step"),
        total      = result.get("total"),
    )


@app.post("/onboard/answer", response_model=OnboardResponse, tags=["Onboarding"])
def onboard_answer(req: OnboardAnswerRequest):
    """
    Submit one onboarding button answer. Returns next question or
    completion payload (with eco score + diagnosis).
    """
    session = get_or_create_session(req.session_id)
    agent: GreenMindAgent = session["agent"]

    if agent.onboarding_phase != GreenMindAgent.PHASE_ONBOARDING:
        raise HTTPException(
            status_code=400,
            detail="Session is not in onboarding phase. Call /onboard/start first."
        )

    result = agent.advance_onboarding(req.answer)

    return OnboardResponse(
        session_id = req.session_id,
        type       = result["type"],
        message    = result["message"],
        buttons    = result.get("buttons"),
        step       = result.get("step"),
        total      = result.get("total"),
        eco_score  = result.get("eco_score"),
        diagnosis  = result.get("diagnosis"),
        profile    = result.get("profile"),
    )


# -----------------------------------------------------------------
# Endpoints — Eco Score
# -----------------------------------------------------------------

@app.get("/eco_score/{session_id}", tags=["Eco Score"])
def get_eco_score(session_id: str):
    """Return the eco score for a completed onboarding session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    agent: GreenMindAgent = sessions[session_id]["agent"]

    if not agent.onboarding_profile:
        raise HTTPException(
            status_code=400,
            detail="Onboarding not complete — eco score not yet available."
        )

    return {
        "session_id": session_id,
        "profile":    agent.onboarding_profile,
        **compute_eco_score(agent.onboarding_profile),
    }


# -----------------------------------------------------------------
# Endpoints — Habit Tracker
# -----------------------------------------------------------------

@app.post("/habit/activate", tags=["Habit Tracker"])
def activate_habit(req: HabitActivateRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    agent: GreenMindAgent = sessions[req.session_id]["agent"]
    agent.activate_habit_tracker()

    return {
        "session_id": req.session_id,
        "activated":  True,
        "tracking":   agent.habit_tracker,
    }


@app.post("/habit/log", tags=["Habit Tracker"])
def log_habit(req: HabitLogRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    agent: GreenMindAgent = sessions[req.session_id]["agent"]
    agent.log_habit_day(tried_first=req.tried_first, retries=req.retries)

    return {
        "session_id": req.session_id,
        "logged":     True,
        "summary":    agent.get_habit_summary(),
    }


@app.get("/habit/summary/{session_id}", tags=["Habit Tracker"])
def habit_summary(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    agent: GreenMindAgent = sessions[session_id]["agent"]
    summary = agent.get_habit_summary()

    return {"session_id": session_id, **summary}


# -----------------------------------------------------------------
# Endpoints — Chat
# -----------------------------------------------------------------

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(req: ChatRequest):

    session_id = req.session_id or str(uuid.uuid4())

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session    = get_or_create_session(session_id)
    agent:      GreenMindAgent = session["agent"]
    history:    list           = session["history"]
    log_writer: LogWriter      = session["log"]

    raw_response, log = agent.get_response(req.message, history)

    # Detect structured payloads
    structured = None
    display_response = raw_response

    if raw_response.startswith('{"__structured__"'):
        try:
            parsed       = json.loads(raw_response)
            structured   = parsed.get("__structured__", {})
            display_response = structured.get("message", "")
        except json.JSONDecodeError:
            pass

    history.append(f"Student: {req.message}")
    history.append(f"GreenMind: {display_response}")

    log_writer.write(log)

    classification = log.get("classification", {}).get("result", "none")
    if classification not in VALID_MODES:
        classification = "none"

    return ChatResponse(
        session_id     = session_id,
        response       = display_response,
        active_mode    = agent.state,
        classification = classification,
        structured     = structured,
    )


# -----------------------------------------------------------------
# Endpoints — Session management
# -----------------------------------------------------------------

@app.post("/reset", response_model=ResetResponse, tags=["Session"])
def reset(req: ResetRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    sessions[req.session_id]["history"] = []
    sessions[req.session_id]["agent"]   = GreenMindAgent()

    return ResetResponse(
        session_id = req.session_id,
        message    = "Session reset. Conversation history cleared.",
    )


@app.get("/state/{session_id}", response_model=StateResponse, tags=["Session"])
def state(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    session = sessions[session_id]
    agent: GreenMindAgent = session["agent"]

    return StateResponse(
        session_id       = session_id,
        active_mode      = agent.state,
        history_length   = len(session["history"]),
        onboarding_phase = agent.onboarding_phase,
        habit_activated  = agent.habit_tracker["activated"],
    )


# -----------------------------------------------------------------
# Run directly
# -----------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
