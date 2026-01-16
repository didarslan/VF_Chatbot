from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from vfa.core.config import settings

IntentType = Literal["DEVICE_DISCOVERY", "DEVICE_SELECTION", "ORDER_CREATE", "KNOWLEDGE_5G", "OTHER"]

class IntentResult(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0, le=1)
    selected_model: Optional[str] = None
    required_slots: List[str] = []

_llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0.0,
    api_key=settings.openai_api_key,
).with_structured_output(IntentResult)

SYSTEM = """You are an intent classifier for a Vodafone customer assistant.
Classify the user's message into one of:
- DEVICE_DISCOVERY: user wants recommendations/options for 5G phones
- DEVICE_SELECTION: user picks a specific phone model
- ORDER_CREATE: user wants to create/confirm an order (buy/order/subscribe)
- KNOWLEDGE_5G: user asks about 5G info/coverage/how-to
- OTHER

If user says "X almak istiyorum" or clearly chooses a model => DEVICE_SELECTION or ORDER_CREATE depending on wording.
Return required_slots if order needs more info, e.g. ["installment","city"].
"""

def analyze_intent(user_text: str) -> IntentResult:
    prompt = f"{SYSTEM}\n\nUser message: {user_text}"
    return _llm.invoke(prompt)

