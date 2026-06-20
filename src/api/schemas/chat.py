from pydantic import BaseModel

class ChatRequest(BaseModel):
    input_text: str
    history: list[dict[str, str]] = []

class ChatResponse(BaseModel):
    reply: str
