from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_connection_string: str
    events_provider_base_url: str
    events_provider_api_key: str

    outbox_poll_interval_seconds: int = 10
    outbox_batch_size: int = 50
    outbox_max_attempts: int = 30

    capashino_base_url: str
    capashino_api_key: str

    sentry_dsn: str | None = None

    idempotency_key_ttl_days: int = 7
    idempotency_cleanup_interval_seconds: int = 3600

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def sqlalchemy_url(self) -> str:
        return self.postgres_connection_string.replace(
            "postgres://",
            "postgresql+asyncpg://",
            1,
        )


settings = Settings()
