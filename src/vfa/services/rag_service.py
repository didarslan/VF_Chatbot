from __future__ import annotations

from typing import List, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from vfa.core.config import settings
from vfa.core.prompts import KNOWLEDGE_SYSTEM
from vfa.services.vector_store_factory import get_vectorstore
from vfa.services.llm_factory import make_chat_llm, paced_invoke

class RAGService:
    def __init__(self):
        self.vs = get_vectorstore()
        self.llm = make_chat_llm(model=settings.model, temperature=0.6)

    def retrieve(self, query: str, k: int = 4) -> List[Document]:
        retriever = self.vs.as_retriever(search_kwargs={"k": k})
        return retriever.get_relevant_documents(query)

    def answer(self, question: str) -> Tuple[str, List[str]]:
        docs = self.retrieve(question, k=4)
        if not docs:
            return "Bu konuda bilgi sahibi deÄŸilim.", []

        sources: List[str] = []
        ctx_parts = []
        for i, d in enumerate(docs):
            url = (d.metadata or {}).get("source_url")
            if url and url not in sources:
                sources.append(url)
            ctx_parts.append(f"[{i+1}] {d.page_content[:1000]}")

        context = "\n\n".join(ctx_parts)

        prompt = f"""{KNOWLEDGE_SYSTEM}

Context:
{context}

Soru:
{question}

YanÄ±t:"""
        resp = paced_invoke(self.llm, prompt)
        return resp.content, sources

