"""Launcher script — sets env vars and starts uvicorn."""
import os
import sys

os.environ.setdefault("JWT_SECRET", "dev-secret-key-for-testing-change-in-production-12345678")
os.environ.setdefault("ENABLE_DEMO_DATA", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("HALLUCINATION_CHECK", "true")

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting NEURO_PREDICT_SYS on port {port}...")
    print(f"JWT_SECRET set: {'yes' if os.environ.get('JWT_SECRET') else 'no'}")
    print(f"DEMO_MODE: {not bool(os.environ.get('SUPABASE_URL'))}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=os.getenv("DEBUG", "false").lower() == "true")
