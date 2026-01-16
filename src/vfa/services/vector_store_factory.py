from __future__ import annotations

from vfa.core.config import settings
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma


def get_embeddings() -> OpenAIEmbeddings:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY boş. .env dosyanı kontrol et.")
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        openai_api_key=settings.openai_api_key,
    )


def get_vectorstore() -> Chroma:
    embeddings = get_embeddings()
    return Chroma(
        collection_name=settings.vector_collection,
        embedding_function=embeddings,
        persist_directory=settings.chroma_dir,
    )

