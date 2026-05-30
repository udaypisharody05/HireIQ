from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_name: str = "HireIQ API"
    version: str = "0.1.0"
    database_url: str = Field(
        default="postgresql+psycopg://hireiq:hireiq@localhost:5432/hireiq",
        alias="DATABASE_URL",
    )
    api_cors_origins: str = Field(default="http://localhost:3000", alias="API_CORS_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


settings = Settings()
