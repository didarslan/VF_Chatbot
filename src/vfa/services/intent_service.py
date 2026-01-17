from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from vfa.services.llm_factory import make_chat_llm, paced_invoke, is_llm_disabled, is_quota_error

IntentType = Literal[
    "DEVICE_DISCOVERY",
    "DEVICE_SELECTION",
    "ORDER_CREATE",
    "ORDER_HOWTO",
    "KNOWLEDGE_5G",
    "OTHER",
]

class IntentResult(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0, le=1)
    selected_model: Optional[str] = None
    required_slots: List[str] = []

_llm = make_chat_llm(temperature=0.0) 

SYSTEM = """You are an intent classifier for a Vodafone customer assistant.
Classify the user's message into one of:

- DEVICE_DISCOVERY: user wants recommendations/options for 5G phones (e.g., "5g uyumlu telefon Ã¶ner")
- DEVICE_SELECTION: user picks a specific phone model (e.g., "Samsung Galaxy S25 FE 5G", "Tecno Spark Slim 5G")
- ORDER_CREATE: user is ready to buy / asks to place an order for a specific model (e.g., "S25 FE 5G satÄ±n al", "sipariÅŸ ver")
- ORDER_HOWTO: user asks HOW the ordering process works or what they should do (e.g., "faturaya ek sipariÅŸ nasÄ±l oluÅŸtururum?", "nasÄ±l satÄ±n alÄ±rÄ±m?")
- KNOWLEDGE_5G: user asks about 5G information (coverage, compatibility, SIM, activation, speed tests, etc.)
- OTHER: greetings, chitchat, unrelated

Rules:
1) If the user asks "nasÄ±l / nasÄ±l yaparÄ±m / nasÄ±l oluÅŸtururum" about ordering => ORDER_HOWTO (NOT ORDER_CREATE).
2) If the message contains a clear phone model name without asking for options => DEVICE_SELECTION.
3) ORDER_CREATE requires purchase intent AND a specific model or a product URL in the message OR already selected in conversation (but you only see the message; if not present, prefer DEVICE_SELECTION).
4) If user asks about 5G generally => KNOWLEDGE_5G.
5) Confidence: 0 to 1. Use 0.9+ when very clear.
6) selected_model: extract the model name if present (e.g., "Samsung Galaxy S25 FE 5G").
7) required_slots: only when intent is ORDER_CREATE and user likely needs missing info: ["installment","city"].
Return JSON only.
"""


def analyze_intent(user_text: str) -> IntentResult:
    if is_llm_disabled():
        return IntentResult(intent="OTHER", confidence=0.0)

    # 1. Mesaj listesini olusturun
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_text},
    ]
    chain = _llm.with_structured_output(IntentResult)
    try:
        return paced_invoke(chain, messages)
    except Exception as e:
        if is_quota_error(e) or "llm disabled" in str(e).lower():
            return IntentResult(intent="OTHER", confidence=0.0)
        raise

