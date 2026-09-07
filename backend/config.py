"""
NEURO_PREDICT_SYS Backend Configuration
Handles Supabase connection, JWT auth, and app settings.
"""
import os
from functools import lru_cache


class Settings:
    """Application settings - reads from env vars with sensible defaults."""

    # App
    APP_NAME: str = "NEURO_PREDICT_SYS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # JWT Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "neuro-predict-sys-dev-secret-key-change-in-prod")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Demo mode - when True, uses in-memory storage instead of Supabase
    DEMO_MODE: bool = not bool(os.getenv("SUPABASE_URL"))

    # CORS
    CORS_ORIGINS: list = ["*"]

    # ML Model paths
    MODEL_DIR: str = os.path.join(os.path.dirname(__file__), "models")
    TRAINED_MODEL_PATH: str = os.path.join(MODEL_DIR, "trained_model.pkl")
    SCALER_PATH: str = os.path.join(MODEL_DIR, "scaler.pkl")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
