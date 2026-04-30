"""
config.py — Central configuration using pydantic-settings.
Reads from environment variables or .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Bot
    bot_token: str
    admin_chat_id: int

    # Database
    database_url: str = "sqlite+aiosqlite:///./roommate_bot.db"

    # Pagination
    page_size: int = 5

    # Logging
    log_level: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
