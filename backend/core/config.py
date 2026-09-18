"""
NEURO_PREDICT_SYS — Unified Configuration
All settings in one place. Reads from env vars with safe defaults.
"""
import os
from functools import lru_cache


class Settings:
    # ── App ──────────────────────────────────────────────────────
    APP_NAME: str = "NEURO_PREDICT_SYS"
    APP_VERSION: str = "3.0.0"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    API_PREFIX: str = "/api/v1"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    ENABLE_DEMO_DATA: bool = os.getenv("ENABLE_DEMO_DATA", "true").lower() == "true"

    # ── JWT Auth ─────────────────────────────────────────────────
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    PASSWORD_RESET_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "60"))

    # ── Supabase ─────────────────────────────────────────────────
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    DEMO_MODE: bool = not bool(os.getenv("SUPABASE_URL"))

    # ── Clerk ────────────────────────────────────────────────────
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")
    CLERK_PUBLISHABLE_KEY: str = os.getenv("CLERK_PUBLISHABLE_KEY", "")
    CLERK_WEBHOOK_SECRET: str = os.getenv("CLERK_WEBHOOK_SECRET", "")

    # ── ML Models ────────────────────────────────────────────────
    MODEL_DIR: str = os.getenv("MODEL_DIR", os.path.join(os.path.dirname(__file__), "..", "ml", "models"))
    TRAINED_MODEL_PATH: str = os.path.join(MODEL_DIR, "trained_model.pkl")
    SCALER_PATH: str = os.path.join(MODEL_DIR, "scaler.pkl")
    METADATA_PATH: str = os.path.join(MODEL_DIR, "model_metadata.pkl")
    DARWIN_MODEL_DIR: str = os.path.join(MODEL_DIR, "darwin")

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_API: str = "60/minute"
    RATE_LIMIT_PREDICT: str = "20/minute"

    # ── Anti-Hallucination ───────────────────────────────────────
    HALLUCINATION_CHECK_ENABLED: bool = os.getenv("HALLUCINATION_CHECK", "true").lower() == "true"
    MAX_INPUT_LENGTH: int = 10000
    ALLOWED_SYMPROMS: list = [
        "memory_loss", "confusion", "disorientation", "difficulty_with_tasks",
        "language_problems", "tremor", "rigidity", "bradykinesia",
        "postural_instability", "speech_changes", "muscle_weakness",
        "fasciculations", "difficulty_speaking", "difficulty_swallowing",
        "cramps", "chorea", "cognitive_decline", "psychiatric_symptoms",
        "motor_impairment", "weight_loss", "seizures", "temporary_confusion",
        "staring_spells", "uncontrollable_jerking", "loss_of_consciousness",
        "numbness", "vision_problems", "fatigue", "walking_difficulty",
        "spasticity", "headache", "nausea", "light_sensitivity", "aura",
        "throbbing_pain", "vision_changes", "personality_changes", "weakness",
    ]

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_LOGIN: int = int(os.getenv("RATE_LIMIT_LOGIN", "10"))  # per minute
    RATE_LIMIT_API: int = int(os.getenv("RATE_LIMIT_API", "120"))    # per minute
    RATE_LIMIT_PREDICT: int = int(os.getenv("RATE_LIMIT_PREDICT", "20"))  # per minute

    # ── Audit Logging ────────────────────────────────────────────
    AUDIT_ENABLED: bool = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "")

    def validate(self):
        """Validate critical settings. Called at startup."""
        errors = []
        if not self.JWT_SECRET or len(self.JWT_SECRET) < 32:
            if self.APP_ENV == "production":
                errors.append("JWT_SECRET must be set to a random string of 32+ chars in production")
            elif not self.JWT_SECRET:
                # Auto-generate for development only
                import secrets
                self.JWT_SECRET = secrets.token_hex(32)
                print(f"[WARNING] Auto-generated JWT_SECRET for development. Set JWT_SECRET env var.")
        if self.APP_ENV == "production" and self.ENABLE_DEMO_DATA:
            errors.append("ENABLE_DEMO_DATA must be false in production")
        if self.APP_ENV == "production" and "*" in self.CORS_ORIGINS:
            errors.append("CORS_ORIGINS must not contain wildcard in production")
        if errors:
            for e in errors:
                print(f"[FATAL] {e}")
            if self.APP_ENV == "production":
                raise SystemExit("Configuration errors prevent startup in production mode")
        return True

    # ── WebSocket ────────────────────────────────────────────────
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds

    # ── Vercel ───────────────────────────────────────────────────
    VERCEL: bool = os.getenv("VERCEL", "false").lower() == "true"


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    s.validate()
    return s
