from __future__ import annotations

import os
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from vfa.services.llm_factory import make_chat_llm, paced_invoke, is_llm_disabled, is_quota_error

class ResponseDraft(BaseModel):
    answer: str = Field(..., description="Final Turkish reply to user.")


class ResponseComposer:
    def __init__(self):
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        tone = os.getenv("ASSISTANT_TONE", "friendly")
        max_sent = int(os.getenv("ASSISTANT_MAX_SENTENCES", "3"))

        self.llm = make_chat_llm(model=model, temperature=0.6)
        self.max_sent = max_sent
        self.tone = tone

        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a Vodafone Türkiye assistant. Reply ONLY in Turkish.\n"
             "Your job is to write a natural, helpful message based strictly on the given DATA.\n"
             "Do NOT invent prices, specs, campaign terms or any facts not in DATA.\n"
             f"Tone: {tone}. Keep it short: max {max_sent} sentences.\n"
             "If DATA.missing exists, politely ask for them.\n"
             "If intent is GREETING, greet and offer 2-3 things you can do.\n"
             "If order is created, confirm clearly.\n"),
            ("human",
             "INTENT: {intent}\n"
             "ACTION: {action}\n"
             "DATA (json-like): {data}\n"
             "Write the final answer text:")
        ])

    def _fallback_response(self, intent: str, action: str, data: Dict[str, Any]) -> str:
        if action == "GREET":
            return "Merhaba! 5G telefon onerisi, 5G bilgi ve siparis olusturma konularinda yardimci olabilirim."
        if action == "EXPLAIN_ORDER_FLOW":
            steps = data.get("steps") or []
            if steps:
                return " ".join(steps)
            return "Siparis olusturma adimlarini paylasabilirim. Hangi modeli istiyorsunuz?"
        if action == "ASK_SLOTS":
            missing = data.get("missing") or []
            if missing:
                return "Siparis icin su bilgiler gerekli: " + ", ".join(missing)
            return "Siparis icin ek bilgilere ihtiyacim var."
        if action == "ORDER_CREATED":
            parts = ["Siparis olusturuldu."]
            order_id = data.get("order_id")
            if order_id:
                parts.append(f"Order ID: {order_id}.")
            selected_model = data.get("selected_model")
            if selected_model:
                parts.append(f"Model: {selected_model}.")
            installment = data.get("installment")
            if installment:
                parts.append(f"Taksit: {installment}.")
            city = data.get("city")
            if city:
                parts.append(f"Sehir: {city}.")
            return " ".join(parts)
        return "Suan yanit uretemiyorum. Lutfen tekrar deneyin."

    def compose(self, intent: str, action: str, data: Dict[str, Any]) -> str:
        if is_llm_disabled():
            return self._fallback_response(intent, action, data)
        chain = self.prompt | self.llm.with_structured_output(ResponseDraft)
        try:
            out: ResponseDraft = paced_invoke(chain, {
                "intent": intent,
                "action": action,
                "data": data,
            })
            return out.answer.strip()
        except Exception as e:
            if is_quota_error(e) or "llm disabled" in str(e).lower():
                return self._fallback_response(intent, action, data)
            raise
