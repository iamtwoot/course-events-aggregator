from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_connection_string: str

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def sqlalchemy_url(self) -> str:
        return self.postgres_connection_string.replace(
            "postgres://",
            "postgresql+asyncpg://",
            1,
        )


settings = Settings()
