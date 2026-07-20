"""
config.py - Central configuration for CodeMentor AI

Loads environment variables and validates them on startup.
If any required variable is missing, the app refuses to start.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator


# Find the .env file: check backend/ first, then project root
def find_env_file() -> str:
    """Look for .env in current dir, then parent dir (project root)."""
    current = Path(__file__).resolve().parent.parent  # backend/
    if (current / ".env").exists():
        return str(current / ".env")
    project_root = current.parent  # codementor-ai/
    if (project_root / ".env").exists():
        return str(project_root / ".env")
    return ".env"  # fallback


class Settings(BaseSettings):
    """
    All environment variables used by the application.
    Pydantic automatically reads from .env file.
    """

    # --- Required Variables ---

    # OpenRouter API key for accessing Qwen LLM
    openrouter_api_key: str

    # Qdrant Cloud connection URL (required from Phase 2 onwards)
    qdrant_url: str = ""

    # Qdrant Cloud API key (required from Phase 2 onwards)
    qdrant_api_key: str = ""

    # --- Optional Variables ---

    # HuggingFace token (not required for public models)
    hf_token: str = ""

    # Redis connection URL
    redis_url: str = "redis://localhost:6379"

    # --- Application Settings ---

    # Name of the Qdrant collection for storing code chunks
    collection_name: str = "code_chunks"

    # Directory where cloned repos are temporarily stored
    clone_directory: str = "cloned_repos"

    # Maximum file size to process (in bytes) - 100KB
    max_file_size: int = 100_000

    # Maximum number of files to process per repository
    max_files_per_repo: int = 500

    # Embedding model name
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Embedding vector dimension
    embedding_dimension: int = 384

    # LLM model name on OpenRouter
    llm_model: str = "qwen/qwen3-8b"

    # Chunk size in characters (roughly 500 tokens)
    chunk_size: int = 2000

    # Chunk overlap in characters (roughly 50 tokens)
    chunk_overlap: int = 200

    # Number of similar chunks to retrieve
    top_k: int = 5

    # CORS allowed origins
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        """Parse comma-separated string, JSON string, or list into list[str]."""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return ["*"]
            if value.startswith("[") and value.endswith("]"):
                import json
                try:
                    return json.loads(value)
                except Exception:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("openrouter_api_key")
    @classmethod
    def must_not_be_empty(cls, value: str, info) -> str:
        """Make sure required env variables are actually set, not empty strings."""
        if not value or value.strip() == "":
            raise ValueError(f"{info.field_name} cannot be empty. Check your .env file.")
        return value

    class Config:
        env_file = find_env_file()
        env_file_encoding = "utf-8"


# Create a single settings instance used across the entire app
settings = Settings()
