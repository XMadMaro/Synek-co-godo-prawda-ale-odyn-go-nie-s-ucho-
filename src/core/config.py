"""
TruthSeeker - Core Configuration Module
Centralized settings management using Pydantic Settings.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="TS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ==========================================================================
    # General
    # ==========================================================================
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ==========================================================================
    # Database - PostgreSQL
    # ==========================================================================
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "truthseeker"
    postgres_user: str = "truthseeker"
    postgres_password: str = "truthseeker_dev"

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ==========================================================================
    # Vector Database - Qdrant
    # ==========================================================================
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # ==========================================================================
    # Cache - Redis
    # ==========================================================================
    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    # ==========================================================================
    # LLM Configuration
    # ==========================================================================
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4-turbo"
    embedding_model: str = "text-embedding-3-small"

    # ==========================================================================
    # Scraper Configuration
    # ==========================================================================
    scraper_timeout: int = 30
    scraper_max_concurrent: int = 5
    scraper_user_agent: str = "TruthSeeker/1.0"

    # ==========================================================================
    # RAG Configuration
    # ==========================================================================
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50
    rag_top_k: int = 5
    rag_min_similarity: float = 0.7

    # ==========================================================================
    # Auditor Configuration
    # ==========================================================================
    auditor_questions_per_session: int = 20
    auditor_wait_between_questions: int = Field(default=2, description="Seconds")
    judge_confidence_threshold: float = 0.7

    # ==========================================================================
    # API Server
    # ==========================================================================
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
