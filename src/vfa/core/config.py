import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class Settings(BaseModel):
    # OpenAI
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    openai_embedding_model: str = Field(default_factory=lambda: os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"))

    # Vector backend
    vector_backend: str = Field(default_factory=lambda: os.getenv("VECTOR_BACKEND", "milvus"))  # milvus|chroma

    # Zilliz/Milvus
    zilliz_uri: str = Field(default_factory=lambda: os.getenv("ZILLIZ_URI", ""))
    zilliz_token: str = Field(default_factory=lambda: os.getenv("ZILLIZ_TOKEN", ""))
    milvus_collection: str = Field(default_factory=lambda: os.getenv("MILVUS_COLLECTION", "vodafone_kb"))
    milvus_db_name: str = Field(default_factory=lambda: os.getenv("MILVUS_DB_NAME", "default"))

    # Chroma
    chroma_dir: str = Field(default_factory=lambda: os.getenv("CHROMA_DIR", "./data/indexes/chroma"))

    # HTTP
    http_timeout_s: int = Field(default_factory=lambda: int(os.getenv("HTTP_TIMEOUT_S", "20")))
    http_max_retries: int = Field(default_factory=lambda: int(os.getenv("HTTP_MAX_RETRIES", "3")))
    http_rate_limit_rps: float = Field(default_factory=lambda: float(os.getenv("HTTP_RATE_LIMIT_RPS", "1")))
    user_agent: str = Field(default_factory=lambda: os.getenv("USER_AGENT", "VodafoneAgenticAssistant/0.1"))

settings = Settings()