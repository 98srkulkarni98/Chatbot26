"""
api.py — GreenMind REST API
============================
FastAPI server that exposes GreenMindAgent over HTTP.

Endpoints:
  POST /chat          — send a message, get a response
  POST /reset         — reset chat history for a session
  GET  /state/{id}    — current agent state
  GET  /health        — health check
  GET  /modes         — available modes

Run:
  uvicorn api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid

from greenmind import GreenMindAgent, LogWriter

# -----------------------------------------------------------------
# App setup
# -----------------------------------------------------------------

app = FastAPI(
    title="GreenMind API",
    description="Sustainable AI assistant — LLM energy & environmental impact",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # ⚠️ tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------
# In-memory session store
# { session_id -> { agent, history, log } }
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
    session_id: str
    response: str
    active_mode: str
    classification: str


class ResetRequest(BaseModel):
    session_id: str


class ResetResponse(BaseModel):
    session_id: str
    message: str


class StateResponse(BaseModel):
    session_id: str
    active_mode: str
    history_length: int


class HealthResponse(BaseModel):
    status: str
    active_sessions: int


# -----------------------------------------------------------------
# Constants
# -----------------------------------------------------------------

VALID_MODES = {"educator", "calculator", "habit", "none"}


# -----------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    """Check if the API is running."""
    return HealthResponse(status="ok", active_sessions=len(sessions))


@app.get("/modes", tags=["System"])
def get_modes():
    """Return available GreenMind modes."""
    return {"modes": ["educator", "calculator", "habit"]}


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(req: ChatRequest):
    """
    Send a user message and receive a GreenMind response.

    The agent detects intent and switches between:
    educator | calculator | habit
    """

    session_id = req.session_id or str(uuid.uuid4())

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session = get_or_create_session(session_id)

    agent: GreenMindAgent = session["agent"]
    history: list = session["history"]
    log_writer: LogWriter = session["log"]

    # Generate response
    response, log = agent.get_response(req.message, history)

    # Update history
    history.append(f"User: {req.message}")
    history.append(f"GreenMind: {response}")

    # Persist log
    log_writer.write(log)

    # Safe classification extraction
    classification = log.get("classification", {}).get("result", "none")
    if classification not in VALID_MODES:
        classification = "none"

    return ChatResponse(
        session_id=session_id,
        response=response,
        active_mode=log.get("agent_state", "educator"),
        classification=classification,
    )


@app.post("/reset", response_model=ResetResponse, tags=["Chat"])
def reset(req: ResetRequest):
    """Reset the conversation history for a session."""
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    sessions[req.session_id]["history"] = []
    sessions[req.session_id]["agent"] = GreenMindAgent()

    return ResetResponse(
        session_id=req.session_id,
        message="Session reset. Conversation history cleared.",
    )


@app.get("/state/{session_id}", response_model=StateResponse, tags=["Chat"])
def state(session_id: str):
    """Get current agent mode and history length."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    session = sessions[session_id]

    return StateResponse(
        session_id=session_id,
        active_mode=session["agent"].state,
        history_length=len(session["history"]),
    )


# -----------------------------------------------------------------
# Run directly
# -----------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)