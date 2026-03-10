from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Settings", "get_settings"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "Data Analysis Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./data/app.db"
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_ALWAYS_EAGER: bool = True
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # R Plumber
    R_PLUMBER_BASE_URL: str = "http://localhost:8787"
    R_PLUMBER_TIMEOUT: float = 120.0

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File storage
    UPLOAD_ROOT: Path = Path("./data/uploads")
    ARTIFACT_ROOT: Path = Path("./data/artifacts")
    MAX_UPLOAD_SIZE_MB: int = 50

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def sqlite_url(self) -> str:
        return self.DATABASE_URL

    def ensure_dirs(self) -> None:
        self.UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
        self.ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
        Path(self.DATABASE_URL.replace("sqlite:///", "")).parent.mkdir(
            parents=True, exist_ok=True
        )


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
