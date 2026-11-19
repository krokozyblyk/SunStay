from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SunStay API"
    app_env: str = "development"
    api_prefix: str = "/api"

    database_url: str = "postgresql://sunstay_app:sunstay_app@localhost:5432/hotel"
    database_admin_url: str = "postgresql://postgres:postgres@localhost:5432/hotel"
    analytics_database_url: str = "postgresql://sunstay_analytics:sunstay_analytics@localhost:5432/hotel"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7

    data_encryption_key: str = "bh9O5gpBkH-qPkJSoUkiWswjQyQqWcQ7ZHZU6BO_C9s="
    backup_file_name: str = "sunstay_latest.dump"

    cors_origins: str = "http://localhost:5173,http://localhost:8080,http://localhost"
    backup_dir: str = "/backups"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
