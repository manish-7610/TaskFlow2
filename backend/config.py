from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App metadata
    APP_NAME: str = "TaskFlow2"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./taskflow.db"

    # CORS – comma-separated allowed origins
    # Use "*" for open dev access, or list explicit origins for production
    FRONTEND_ORIGIN: str = (
        "http://localhost:5500,http://127.0.0.1:5500,"
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:8080,http://127.0.0.1:8080,"
        "http://localhost:8000,http://127.0.0.1:8000,"
        "null"          # file:// protocol (opening HTML directly from disk)
    )

    @field_validator("FRONTEND_ORIGIN", mode="before")
    @classmethod
    def parse_origins(cls, v: str) -> str:
        return v

    @property
    def cors_origins(self) -> List[str]:
        """Return the list of allowed CORS origins, computed fresh each call."""
        return [
            origin.strip()
            for origin in self.FRONTEND_ORIGIN.split(",")
            if origin.strip()
        ]

    @property
    def cors_allow_all(self) -> bool:
        """Return True when DEBUG mode is on – allows any origin for easy local dev."""
        return self.DEBUG

    # Logging
    LOG_LEVEL: str = "INFO"

    # AI
    USE_REAL_LLM: bool = False
    LLM_API_KEY: str | None = None

    # Security / JWT
    SECRET_KEY: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


# Singleton settings instance
settings = Settings()
