"""
NEURO_PREDICT_SYS — Unified Authentication (v3)
JWT access + refresh tokens, RBAC, rate limiting, brute-force protection.
"""
import os
import uuid
import time
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Callable
from functools import wraps

from fastapi import Depends, HTTPException, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt

from .config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


# ── Rate Limiter (in-memory, production should use Redis) ─────────

class RateLimiter:
    """Simple in-memory sliding window rate limiter."""

    def __init__(self):
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        now = time.time()
        if key not in self._requests:
            self._requests[key] = []
        # Remove old entries outside the window
        self._requests[key] = [t for t in self._requests[key] if now - t < window_seconds]
        if len(self._requests[key]) >= max_requests:
            return False
        self._requests[key].append(now)
        return True

    def get_remaining(self, key: str, max_requests: int, window_seconds: int = 60) -> int:
        now = time.time()
        if key not in self._requests:
            return max_requests
        recent = [t for t in self._requests[key] if now - t < window_seconds]
        return max(0, max_requests - len(recent))

    def get_retry_after(self, key: str, window_seconds: int = 60) -> int:
        if key not in self._requests or not self._requests[key]:
            return 0
        oldest = min(self._requests[key])
        return max(0, int(window_seconds - (time.time() - oldest)))


rate_limiter = RateLimiter()


def require_rate_limit(max_requests: int, window_seconds: int = 60, key_prefix: str = "api"):
    """Dependency: enforce rate limiting on an endpoint."""
    async def _check(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{key_prefix}:{client_ip}"
        if not rate_limiter.is_allowed(key, max_requests, window_seconds):
            retry_after = rate_limiter.get_retry_after(key, window_seconds)
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )
    return _check


# ── Password Helpers ──────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def generate_refresh_token() -> str:
    """Generate a cryptographically random refresh token."""
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    """Hash a token for secure storage (SHA-256)."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── JWT Helpers ───────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
        "token_type": "access",
    })
    if not settings.JWT_SECRET:
        raise RuntimeError("JWT_SECRET must be set")
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict, token_family: str = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
        "token_type": "refresh",
        "family": token_family or str(uuid.uuid4()),
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    if not settings.JWT_SECRET:
        raise HTTPException(status_code=500, detail="JWT_SECRET not configured")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Demo Accounts (development only) ──────────────────────────────

DEMO_ACCOUNTS = [
    {"id": "demo-admin-001", "email": "admin@neuropredict.sys", "password": "admin123",
     "full_name": "Dr. Sarah Chen", "role": "admin", "department": "Neurology", "clearance_level": 5},
    {"id": "demo-neuro-001", "email": "neuro@neuropredict.sys", "password": "neuro123",
     "full_name": "Dr. James Wilson", "role": "neurologist", "department": "Neurology", "clearance_level": 4},
    {"id": "demo-pharm-001", "email": "pharma@neuropredict.sys", "password": "pharma123",
     "full_name": "Dr. Priya Sharma", "role": "pharmacist", "department": "Pharmacy", "clearance_level": 3},
    {"id": "demo-surg-001", "email": "surgery@neuropredict.sys", "password": "surgery123",
     "full_name": "Dr. Marcus Thompson", "role": "surgeon", "department": "Neurosurgery", "clearance_level": 4},
    {"id": "demo-research-001", "email": "research@neuropredict.sys", "password": "research123",
     "full_name": "Dr. Elena Volkov", "role": "researcher", "department": "Research", "clearance_level": 3},
    {"id": "demo-user-001", "email": "demo@neuropredict.sys", "password": "demo123",
     "full_name": "Demo User", "role": "demo", "department": None, "clearance_level": 1},
]


def seed_demo_accounts():
    """Insert demo accounts into the database (development only)."""
    if not settings.ENABLE_DEMO_DATA:
        return
    from .database import get_db
    db = get_db()
    for account in DEMO_ACCOUNTS:
        existing = db.get("users", account["id"])
        if not existing:
            db.insert("users", {
                "id": account["id"],
                "email": account["email"],
                "password_hash": hash_password(account["password"]),
                "full_name": account["full_name"],
                "role": account["role"],
                "department": account["department"],
                "clearance_level": account["clearance_level"],
                "is_active": True,
            })


# ── Permission Model ──────────────────────────────────────────────

# Role hierarchy: higher number = more permissions
ROLE_HIERARCHY = {
    "demo": 1,
    "researcher": 2,
    "pharmacist": 3,
    "neurologist": 4,
    "surgeon": 4,
    "admin": 5,
}

# Permission definitions
PERMISSIONS = {
    "patient.read": ["admin", "neurologist", "surgeon", "pharmacist", "researcher"],
    "patient.write": ["admin", "neurologist", "surgeon"],
    "patient.delete": ["admin"],
    "diagnosis.read": ["admin", "neurologist", "surgeon"],
    "diagnosis.write": ["admin", "neurologist", "surgeon"],
    "analysis.run": ["admin", "neurologist", "researcher"],
    "analysis.read": ["admin", "neurologist", "researcher", "surgeon"],
    "eeg.read": ["admin", "neurologist", "researcher"],
    "eeg.write": ["admin", "neurologist"],
    "pharmacy.read": ["admin", "pharmacist"],
    "pharmacy.write": ["admin", "pharmacist"],
    "prescription.create": ["admin", "neurologist", "surgeon"],
    "prescription.dispense": ["admin", "pharmacist"],
    "ot.read": ["admin", "neurologist", "surgeon"],
    "ot.schedule": ["admin", "surgeon"],
    "ot.modify": ["admin", "surgeon"],
    "research.read": ["admin", "neurologist", "researcher"],
    "research.write": ["admin", "researcher"],
    "admin.users.manage": ["admin"],
    "admin.system": ["admin"],
    "audit.read": ["admin"],
}


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    allowed_roles = PERMISSIONS.get(permission, [])
    return role in allowed_roles or role == "admin"


# ── Audit Logger ──────────────────────────────────────────────────

class AuditLogger:
    """In-memory audit logger. In production, write to database."""

    def __init__(self):
        self._events: List[dict] = []

    def log(self, event_type: str, actor_id: str, resource_type: str = None,
            resource_id: str = None, action: str = None, result: str = "success",
            metadata: dict = None, request: Request = None):
        event = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "actor_id": actor_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "result": result,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ip_address": request.client.host if request and request.client else None,
        }
        self._events.append(event)
        # In production, persist to database here
        return event

    def get_events(self, limit: int = 100, actor_id: str = None,
                   event_type: str = None) -> List[dict]:
        events = self._events
        if actor_id:
            events = [e for e in events if e["actor_id"] == actor_id]
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        return events[-limit:]


audit_logger = AuditLogger()


# ── Security Dependencies ─────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    request: Request = None,
) -> dict:
    """
    Extract current user from request.
    Tries: 1) Clerk JWT, 2) Access token, 3) Demo auto-login (dev only).
    """
    from .database import get_db

    # Try Clerk first
    if settings.CLERK_SECRET_KEY:
        try:
            from .clerk import verify_clerk_token
            auth_header = request.headers.get("Authorization", "") if request else ""
            if auth_header.startswith("Bearer "):
                clerk_user = await verify_clerk_token(auth_header[7:])
                if clerk_user:
                    return clerk_user
        except Exception:
            pass

    # Try access token
    if credentials:
        payload = decode_jwt(credentials.credentials)
        if payload.get("token_type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        db = get_db()
        user = db.get("users", payload.get("sub", ""))
        if not user or not user.get("is_active"):
            raise HTTPException(status_code=401, detail="User not found or disabled")
        return {k: v for k, v in user.items() if k != "password_hash"}

    # Demo auto-login (development only)
    if settings.DEMO_MODE and settings.ENABLE_DEMO_DATA:
        db = get_db()
        admin = db.get("users", "demo-admin-001")
        if admin:
            return {k: v for k, v in admin.items() if k != "password_hash"}

    raise HTTPException(status_code=401, detail="Not authenticated")


async def require_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_role(*roles: str):
    """Dependency factory: require one of the specified roles."""
    async def _check(user=Depends(get_current_user)):
        if user.get("role") not in roles and user.get("role") != "admin":
            raise HTTPException(status_code=403, detail=f"Required role: {', '.join(roles)}")
        return user
    return _check


def require_permission(permission: str):
    """Dependency factory: require a specific permission."""
    async def _check(user=Depends(get_current_user)):
        if not has_permission(user.get("role", ""), permission):
            raise HTTPException(status_code=403, detail=f"Permission denied: {permission}")
        return user
    return _check


def require_any_role(*roles: str):
    """Dependency factory: require any one of the specified roles."""
    async def _check(user=Depends(get_current_user)):
        user_role = user.get("role", "")
        if user_role not in roles and user_role != "admin":
            raise HTTPException(status_code=403, detail=f"One of these roles required: {', '.join(roles)}")
        return user
    return _check


def require_clearance_level(min_level: int):
    """Dependency factory: require minimum clearance level."""
    async def _check(user=Depends(get_current_user)):
        user_level = user.get("clearance_level", 1)
        if user_level < min_level and user.get("role") != "admin":
            raise HTTPException(status_code=403, detail=f"Clearance level {min_level} required")
        return user
    return _check
