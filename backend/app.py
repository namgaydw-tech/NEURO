"""
NEURO_PREDICT_SYS v2 — Unified FastAPI Application
WebSocket hub, all modules interconnected, anti-hallucination middleware.
"""
import os
import sys
import time
import json
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import get_settings
from core.database import get_db
from core.websocket import manager, WSEvent
from core.auth import seed_demo_accounts, get_current_user, create_access_token, verify_password, DEMO_ACCOUNTS, hash_password
from core.anti_hallucination import validator, hallucination_detector, proxy_shield
from routes import router

settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"\n{'='*60}")
    print(f"  NEURO_PREDICT_SYS v{settings.APP_VERSION}")
    print(f"  Mode: {'DEMO (in-memory)' if settings.DEMO_MODE else 'PRODUCTION (Supabase)'}")
    print(f"  Clerk: {'ENABLED' if settings.CLERK_SECRET_KEY else 'DISABLED'}")
    print(f"  Anti-Hallucination: {'ON' if settings.HALLUCINATION_CHECK_ENABLED else 'OFF'}")
    print(f"  API: http://localhost:8000{settings.API_PREFIX}")
    print(f"  WS:  ws://localhost:8000/ws/{{module}}")
    print(f"{'='*60}\n")

    seed_demo_accounts()
    try:
        from seed import seed_all
        seed_all()
    except Exception:
        pass

    manager.start_heartbeat()
    yield
    print("\n[NEURO_PREDICT_SYS] Shutting down...")


# ── App ───────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Neuroscience AI Disease Prediction System — Unified Backend",
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


# ── Request Logging Middleware ─────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    if request.url.path.startswith("/api/"):
        asyncio.create_task(manager.broadcast("dashboard", {
            "type": WSEvent.SYSTEM_LOG,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration, 1),
            "ts": time.time(),
        }))
    return response


# ── Anti-Hallucination Middleware ──────────────────────────────────

@app.middleware("http")
async def anti_hallucination_middleware(request: Request, call_next):
    if not settings.HALLUCINATION_CHECK_ENABLED:
        return await call_next(request)
    if request.method in ("POST", "PUT") and "application/json" in request.headers.get("content-type", ""):
        try:
            body = await request.body()
            if body:
                scan = proxy_shield.scan(body.decode("utf-8", errors="ignore"))
                if scan["blocked"]:
                    asyncio.create_task(manager.broadcast("dashboard", {
                        "type": WSEvent.SYSTEM_ALERT,
                        "alert_type": "proxy_injection_blocked",
                        "path": request.url.path,
                        "attacks": scan["attacks"],
                        "ts": time.time(),
                    }))
                    return JSONResponse(status_code=400, content={"detail": "Input validation failed", "reasons": scan["attacks"]})
        except Exception:
            pass
    return await call_next(request)


# ── Security Headers Middleware ─────────────────────────────────

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # Don't cache private medical data
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    if settings.APP_ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ── API Routes ────────────────────────────────────────────────────

app.include_router(router, prefix=settings.API_PREFIX)


# ── Refresh Token Endpoint ──────────────────────────────────────

from pydantic import BaseModel
from core.auth import create_refresh_token, decode_jwt, create_access_token
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_bearer = HTTPBearer(auto_error=False)


class RefreshRequest(BaseModel):
    refresh_token: str


@app.post(f"{settings.API_PREFIX}/auth/refresh")
async def refresh_token(body: RefreshRequest):
    """Exchange a refresh token for a new access + refresh token pair."""
    try:
        payload = decode_jwt(body.refresh_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if payload.get("token_type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    db = get_db()
    user = db.get("users", payload.get("sub", ""))
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail="User not found or disabled")

    new_access = create_access_token({"sub": user["id"], "role": user["role"]})
    new_refresh = create_refresh_token({"sub": user["id"], "role": user["role"]})

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@app.get(f"{settings.API_PREFIX}/auth/demo-login")
async def demo_quick_login(email: str = "admin@neuropredict.sys"):
    """Quick login for demo mode — returns token pair without password."""
    if not settings.DEMO_MODE or not settings.ENABLE_DEMO_DATA:
        raise HTTPException(status_code=403, detail="Demo login not available in production")
    db = get_db()
    users = db.get_all("users")
    user = next((u for u in users if u.get("email") == email), None)
    if not user:
        raise HTTPException(status_code=404, detail="Demo account not found")
    access = create_access_token({"sub": user["id"], "role": user["role"]})
    refresh = create_refresh_token({"sub": user["id"], "role": user["role"]})
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {k: v for k, v in user.items() if k != "password_hash"},
    }


# ── Clerk Sync Endpoint ─────────────────────────────────────────

class ClerkSyncRequest(BaseModel):
    clerk_user_id: str
    email: str
    full_name: str = ""
    first_name: str = ""
    last_name: str = ""


@app.post(f"{settings.API_PREFIX}/auth/clerk-sync")
async def clerk_sync(body: ClerkSyncRequest, request: Request):
    """
    Upsert a user from Clerk session.
    If user exists by clerk_user_id, return their token.
    If user exists by email, link them.
    If user is new, create a pending-role account.
    """
    if not settings.CLERK_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Clerk not configured")

    db = get_db()
    users = db.get_all("users")

    # Find by clerk_user_id first
    user = next((u for u in users if u.get("clerk_user_id") == body.clerk_user_id), None)

    # Find by email
    if not user:
        user = next((u for u in users if u.get("email") == body.email), None)
        if user:
            # Link Clerk ID to existing account
            db.update("users", user["id"], {"clerk_user_id": body.clerk_user_id})
            user["clerk_user_id"] = body.clerk_user_id

    # Create new account
    if not user:
        import uuid
        user_data = {
            "id": str(uuid.uuid4()),
            "clerk_user_id": body.clerk_user_id,
            "email": body.email,
            "full_name": body.full_name or f"{body.first_name} {body.last_name}".strip() or body.email,
            "first_name": body.first_name,
            "last_name": body.last_name,
            "role": "demo",
            "requested_role": None,
            "role_status": "pending",
            "department": None,
            "clearance_level": 1,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        db.insert("users", user_data)
        user = user_data

    # Issue JWT
    access = create_access_token({"sub": user["id"], "role": user["role"]})
    refresh = create_refresh_token({"sub": user["id"], "role": user["role"]})

    from core.auth import audit_logger
    audit_logger.log("auth.clerk_sync", user["id"], "auth", result="success", request=request)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {k: v for k, v in user.items() if k not in ("password_hash",)},
    }


# ── WebSocket Endpoint ────────────────────────────────────────────

@app.websocket("/ws/{module}")
async def websocket_endpoint(websocket: WebSocket, module: str):
    user_id = websocket.query_params.get("user_id", "anonymous")
    await manager.connect(websocket, module, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "")

                if msg_type == "inter_module":
                    target = msg.get("target_module")
                    payload = {
                        "type": "inter_module_message",
                        "from_module": module,
                        "from_user": user_id,
                        "payload": msg.get("payload", {}),
                        "ts": time.time(),
                    }
                    if target:
                        await manager.broadcast(target, payload)
                    else:
                        await manager.broadcast_all(payload, exclude=websocket)

                elif msg_type == "ping":
                    await manager._send_to_ws(websocket, {"type": "pong", "ts": time.time()})

                elif msg_type == "subscribe":
                    await manager._send_to_ws(websocket, {
                        "type": "subscribed",
                        "target_module": msg.get("target_module"),
                        "ts": time.time(),
                    })

                else:
                    await manager.broadcast(module, {
                        "type": "user_message",
                        "user_id": user_id,
                        "data": msg,
                        "ts": time.time(),
                    }, exclude=websocket)

            except json.JSONDecodeError:
                await manager._send_to_ws(websocket, {"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, module)
        await manager.broadcast(module, {
            "type": "user_left",
            "user_id": user_id,
            "total_users": manager.get_count(module),
        })


# ── Health & Status ───────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "mode": "demo" if settings.DEMO_MODE else "production",
        "websocket_modules": manager.get_modules(),
        "active_connections": manager.get_count(),
    }


@app.get("/api/v1/system/status")
async def system_status():
    db = get_db()
    return {
        "database": "in-memory" if settings.DEMO_MODE else "supabase",
        "clerk": bool(settings.CLERK_SECRET_KEY),
        "anti_hallucination": settings.HALLUCINATION_CHECK_ENABLED,
        "ml_model": os.path.exists(settings.TRAINED_MODEL_PATH),
        "darwin_model": os.path.isdir(settings.DARWIN_MODEL_DIR),
        "patients": db.count("patients"),
        "analyses": db.count("analyses"),
        "diagnoses": db.count("diagnoses"),
        "active_ws_connections": manager.get_count(),
        "ws_modules": manager.get_modules(),
    }


# ── Serve Frontend ────────────────────────────────────────────────

if not settings.VERCEL:
    frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.isdir(frontend_dir):
        from fastapi.staticfiles import StaticFiles
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


# ── Entry Point ───────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=settings.DEBUG)
