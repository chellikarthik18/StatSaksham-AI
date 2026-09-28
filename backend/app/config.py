"""
Central configuration for the StatSaksham AI backend.
All values are read from environment variables (see .env.example).
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional; if it's not installed the process
    # environment (or defaults below) is used instead.
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # --- Database (MySQL only, per project requirements) ---
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "statsaksham")

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        override = os.getenv("DATABASE_URL")
        if override:
            return override
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

    # --- CORS ---
    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5500,http://127.0.0.1:5500,http://localhost:5501,http://127.0.0.1:5501",
        ).split(",")
        if origin.strip()
    ]

    # --- File uploads ---
    UPLOAD_DIR: Path = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")

    # --- Optional LLM configuration (never exposed to the frontend) ---
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "")  # "" = use local deterministic generator
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")

    APP_NAME: str = "StatSaksham AI"
    DEBUG: bool = _get_bool("DEBUG", True)


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
