from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl


class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    DATABASE_URL: AnyUrl

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
