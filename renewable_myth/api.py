from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from renewable_myth import RenewableEnergyMythBuster

app = FastAPI(
    title="Renewable Energy Myth Buster API",
    description="An API for busting common myths about renewable energy.",
    version="1.0.0",
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session-specific agents
session_agents: Dict[str, RenewableEnergyMythBuster] = {}


class ChatMessage(BaseModel):
    message: str
    chat_history: List[str] = []
    session_id: str


class ChatResponse(BaseModel):
    response: str
    topic: str
    log_message: Dict[str, Any]


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    try:
        if chat_message.session_id not in session_agents:
            session_agents[chat_message.session_id] = RenewableEnergyMythBuster()

        agent = session_agents[chat_message.session_id]
        response, log_message = agent.get_response(
            chat_message.message,
            chat_message.chat_history,
        )
        return ChatResponse(
            response=response,
            topic=agent.topic,
            log_message=log_message,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Renewable Energy Myth Buster"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
