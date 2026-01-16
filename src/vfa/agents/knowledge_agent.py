from __future__ import annotations

from vfa.services.rag_service import RAGService

class KnowledgeAgent:
    def __init__(self, rag: RAGService):
        self.rag = rag

    def answer(self, question: str) -> dict:
        answer, sources = self.rag.answer(question)
        return {"answer": answer, "sources": sources}
