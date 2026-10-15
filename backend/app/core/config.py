from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://jobradar:change-me@localhost:5432/jobradar"
    environment: str = "development"
    cors_origins: str = "http://localhost:5173"
    max_upload_size_mb: int = 10
    max_resume_size_mb: int = 10
    development_user_email: str = "local-user@jobradar.test"
    development_user_name: str = "Local User"
    matching_skill_weight: float = Field(default=0.6, ge=0, le=1)
    matching_text_weight: float = Field(default=0.4, ge=0, le=1)

    @model_validator(mode="after")
    def validate_matching_weights(self) -> "Settings":
        if self.matching_skill_weight + self.matching_text_weight <= 0:
            raise ValueError("At least one matching weight must be positive")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
