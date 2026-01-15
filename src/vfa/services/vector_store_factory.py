from vfa.core.config import settings
from langchain_openai import OpenAIEmbeddings

def get_embeddings():
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )

def get_vectorstore():
    embeddings = get_embeddings()
    backend = settings.vector_backend.lower()

    if backend == "milvus":
        # LangChain docs: langchain_milvus.Milvus + connection_args uri/token/db_name :contentReference[oaicite:2]{index=2}
        from langchain_milvus import Milvus
        if not settings.zilliz_uri or not settings.zilliz_token:
            raise ValueError("Zilliz/Milvus için ZILLIZ_URI ve ZILLIZ_TOKEN gerekli (VECTOR_BACKEND=milvus).")

        return Milvus(
            embedding_function=embeddings,
            collection_name=settings.milvus_collection,
            connection_args={"uri": settings.zilliz_uri, "token": settings.zilliz_token, "db_name": settings.milvus_db_name},
            drop_old=False,
        )

    if backend == "chroma":
        from langchain_community.vectorstores import Chroma
        return Chroma(
            collection_name=settings.milvus_collection,
            embedding_function=embeddings,
            persist_directory=settings.chroma_dir,
        )

    raise ValueError(f"Unknown VECTOR_BACKEND: {settings.vector_backend}")
