from typing import List, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from vfa.core.config import settings
from vfa.core.prompts import KNOWLEDGE_SYSTEM
from vfa.services.vector_store_factory import get_vectorstore

class RAGService:
    def __init__(self):
        self.vs = get_vectorstore()
        # ChatOpenAI Responses API destekler :contentReference[oaicite:3]{index=3}
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.2,
            use_responses_api=True,
            output_version="responses/v1",
        )

    def retrieve(self, query: str, k: int = 4) -> List[Document]:
        retriever = self.vs.as_retriever(search_kwargs={"k": k})
        return retriever.get_relevant_documents(query)

    def answer(self, question: str) -> Tuple[str, List[str]]:
        docs = self.retrieve(question, k=4)
        if not docs:
            return "Bu konuda bilgi sahibi değilim.", []

        context = "\n\n".join([f"[{i+1}] {d.page_content[:1200]}" for i, d in enumerate(docs)])
        sources = []
        for d in docs:
            url = (d.metadata or {}).get("source_url")
            if url and url not in sources:
                sources.append(url)

        prompt = f"""{KNOWLEDGE_SYSTEM}

Context:
{context}

Soru:
{question}

Yanıt:"""
        resp = self.llm.invoke(prompt)
        return resp.content, sources
