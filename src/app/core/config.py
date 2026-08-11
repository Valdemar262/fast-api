from functools import lru_cache

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Chancery"
    environment: str = "local"
    debug: bool = False

    postgres_db: str
    postgres_user: str
    postgres_password: SecretStr
    postgres_host: str = "db"
    postgres_port: int = 5432

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: SecretStr

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    @computed_field # type: ignore[misc]
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field # type: ignore[misc]
    @property
    def redis_url(self) -> str:
        pwd = self.redis_password.get_secret_value()
        return f"redis://:{pwd}@{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
