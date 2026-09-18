"""
NEURO_PREDICT_SYS — Main FastAPI Application
Backend for the cyberpunk medical/neuroscience dashboard system.
"""
import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

try:
    from core.config import get_settings
    from core.auth import seed_demo_accounts
    from core.database import get_db
except ImportError:
    from config import get_settings
    from auth import seed_demo_accounts
    from database import get_db
from routes import router
from seed import seed_all

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print(f"\n{'='*60}")
    print(f"  NEURO_PREDICT_SYS v{settings.APP_VERSION}")
    print(f"  Mode: {'DEMO (in-memory)' if settings.DEMO_MODE else 'PRODUCTION (Supabase)'}")
    print(f"  API: http://localhost:8000{settings.API_PREFIX}")
    print(f"{'='*60}\n")

    # Seed demo data
    seed_demo_accounts()
    seed_all()

    yield

    print("\n[NEURO_PREDICT_SYS] Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Neuroscience AI Disease Prediction System — Backend API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(router, prefix=settings.API_PREFIX)

# Serve frontend static files from parent directory
frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level="info",
    )
