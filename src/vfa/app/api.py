from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from vfa.agents.manager import ManagerAgent

router = APIRouter()
manager = ManagerAgent()

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    answer: str
    actions: List[Dict[str, Any]] = []
    state: Dict[str, Any] = {}
    debug: Optional[Dict[str, Any]] = None

@router.post("/chat")
def chat(req: ChatRequest):
    res: ChatResponse = manager.handle(thread_id=req.thread_id, message=req.message)
    return res.model_dump()

