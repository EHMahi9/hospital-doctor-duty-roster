from functools import lru_cache
from typing import Any

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Hospital Doctor Duty Roster API"
    environment: str = "development"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg2://roster:roster@localhost:5432/roster_db"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    backend_cors_origins: list[AnyHttpUrl | str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    first_super_admin_email: str = "superadmin@hospital.bd"
    first_super_admin_password: str = "SuperAdmin@123"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "noreply@hospital.bd"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
