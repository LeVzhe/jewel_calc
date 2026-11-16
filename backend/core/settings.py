from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Jewel calc"
    app_version: str = "1.0.0"
    app_author: str = "LeV"

    postgres_user: str = Field(min_length=1)
    postgres_password: str = Field(min_length=1)
    postgres_db: str = Field(min_length=1)
    postgres_host: str = Field(min_length=1)
    database_port: int = Field(ge=1)

    @property
    def database_url_asyncpg(self) -> str:
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        database = quote_plus(self.postgres_db)
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.postgres_host}:{self.database_port}/{database}"
        )

    R2_ACCESS_KEY_ID: str = Field(min_length=1)
    R2_SECRET_ACCESS_KEY: str = Field(min_length=1)
    R2_ACCOUNT_ID: str = Field(min_length=1)
    R2_BUCKET_NAME: str = Field(min_length=1)
    R2_PUBLIC_BASE_URL: str = Field(min_length=1)

    @property
    def R2_ENDPOINT_URL(self) -> str:
        return f"https://{self.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
