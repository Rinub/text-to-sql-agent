"""
Application configuration — loads settings from .env file.
"""

from pathlib import Path
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # Google Gemini
    GOOGLE_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///data/sample.db"

    # LLM
    LLM_MODEL: str = "gemini-3.6-flash"

    # Agent
    MAX_RETRIES: int = 3

    # App
    APP_TITLE: str = "Self-Healing Text-to-SQL Agent"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Ask questions in plain English and get answers from your database. "
        "Powered by Google Gemini + LangGraph with self-healing SQL generation."
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton settings instance
settings = Settings()
