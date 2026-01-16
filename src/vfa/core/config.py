from __future__ import annotations

import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env once, from project root
load_dotenv()

class Settings(BaseModel):
    # ===== OpenAI =====
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    openai_embedding_model: str = Field(default_factory=lambda: os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"))

    # ===== Vector Store (Chroma) =====
    vector_backend: str = Field(default="chroma")  # fixed for this repo
    vector_collection: str = Field(default_factory=lambda: os.getenv("VECTOR_COLLECTION", "vodafone_kb"))
    chroma_dir: str = Field(default_factory=lambda: os.getenv("CHROMA_DIR", "./data/chroma"))

    # ===== HTTP / Scraping =====
    http_timeout_s: int = Field(default_factory=lambda: int(os.getenv("HTTP_TIMEOUT_S", "20")))
    http_max_retries: int = Field(default_factory=lambda: int(os.getenv("HTTP_MAX_RETRIES", "3")))
    http_rate_limit_rps: float = Field(default_factory=lambda: float(os.getenv("HTTP_RATE_LIMIT_RPS", "1")))
    user_agent: str = Field(default_factory=lambda: os.getenv("USER_AGENT", "VodafoneAgenticAssistant/0.1"))

    def validate_required(self) -> None:
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY boş. .env dosyanı kontrol et.")


settings = Settings()
settings.validate_required()

