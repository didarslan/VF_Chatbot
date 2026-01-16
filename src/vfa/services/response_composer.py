from __future__ import annotations

import os
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class ResponseDraft(BaseModel):
    answer: str = Field(..., description="Final Turkish reply to user.")


class ResponseComposer:
    def __init__(self):
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        tone = os.getenv("ASSISTANT_TONE", "friendly")
        max_sent = int(os.getenv("ASSISTANT_MAX_SENTENCES", "3"))

        self.llm = ChatOpenAI(model=model, temperature=0.6)
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

    def compose(self, intent: str, action: str, data: Dict[str, Any]) -> str:
        chain = self.prompt | self.llm.with_structured_output(ResponseDraft)
        out: ResponseDraft = chain.invoke({
            "intent": intent,
            "action": action,
            "data": data
        })
        return out.answer.strip()
