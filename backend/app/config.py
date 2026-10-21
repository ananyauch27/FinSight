
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 30
    REFRESH_TOKEN_DAYS: int = 14
    CORS_ORIGINS: str = "http://localhost:5173"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 10

    @field_validator("DATABASE_URL")
    @classmethod
    def use_psycopg_driver(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return v.replace(
                "postgres://", "postgresql+psycopg://", 1
            )

        if v.startswith("postgresql://"):
            return v.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )

        return v


settings = Settings()
