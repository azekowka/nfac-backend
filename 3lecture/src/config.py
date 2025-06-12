from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database URLs (async + sync) – overridden automatically when .env is present.
    database_url: str = "postgresql+asyncpg://username:password@db:5432/postgresdb"
    sync_database_url: str = "postgresql://username:password@db:5432/postgresdb"

    # Auth / JWT settings
    secret_key: str = "CHANGE_ME_SUPER_SECRET"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    # Default settings for running inside Docker Compose where the Redis service
    # is reachable via the host name `redis`. These can still be overridden by
    # variables defined in a .env file for local development outside of Docker.
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )


settings = Settings()
