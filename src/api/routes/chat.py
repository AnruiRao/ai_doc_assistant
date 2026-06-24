from fastapi import APIRouter, Request
from api.schemas.chat import ChatRequest, ChatResponse
from agents.react_agent import ReactAgent
from core.async_utils import run_in_thread

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat(request: Request, body: ChatRequest):
    agent = ReactAgent(
        llm=request.app.state.llm,
        tool_registry=request.app.state.tool_registry,
        config=request.app.state.config,
    )
    reply = agent.run(body.input_text, body.history)
    return ChatResponse(reply=reply)