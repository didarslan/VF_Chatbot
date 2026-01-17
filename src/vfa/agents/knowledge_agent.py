from __future__ import annotations
import os
from vfa.services.rag_service import RAGService

class KnowledgeAgent:
    def __init__(self, rag: RAGService):
        self.rag = rag
        self.rag_enabled = os.getenv("RAG_ENABLED", "1") == "1"
        self.topk = int(os.getenv("RAG_TOPK", "5"))

    def answer(self, question: str) -> dict:
        answer, sources = self.rag.answer(question)
        return {"answer": answer, "sources": sources}

    def answer_with_rag_config(self, message: str) -> dict:
        if not self.rag_enabled:
            # retrieval yapmadan direkt LLM ile cevap üret
            return self.llm_answer_only(message)
        else:
            # retrieval + generation
            docs = self.rag.retriever(message, top_k=self.topk)
            return self.rag_answer_with_docs(message, docs)

    def llm_answer_only(self, message: str) -> dict:
        # Implement LLM-only answer logic
        pass

    def rag_answer_with_docs(self, message: str, docs: list) -> dict:
        # Implement RAG answer with documents logic
        pass

