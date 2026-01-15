from fastapi import APIRouter
from pydantic import BaseModel
from vfa.agents.manager import ManagerAgent

router = APIRouter()
manager = ManagerAgent()

class ChatRequest(BaseModel):
    thread_id: str
    message: str

@router.post("/chat")
def chat(req: ChatRequest):
    res = manager.handle(thread_id=req.thread_id, message=req.message)
    return res.model_dump()
