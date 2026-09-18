"""
NEURO_PREDICT_SYS Authentication
JWT-based auth with demo accounts for testing.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    from core.config import get_settings
    from core.database import get_db
except ImportError:
    from config import get_settings
    from database import get_db

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


# ── Password Helpers ───────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT Helpers ────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


# ── Dependencies ───────────────────────────────────────────────────

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    db = get_db()
    user = db.get("users", payload.get("sub", ""))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def require_role(role: str, user=Depends(get_current_user)):
    if user.get("role") != role and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail=f"{role} access required")
    return user


# ── Demo Accounts ──────────────────────────────────────────────────

DEMO_ACCOUNTS = [
    {
        "id": "demo-admin-001",
        "email": "admin@neuropredict.sys",
        "password": "admin123",
        "full_name": "Dr. Sarah Chen",
        "role": "admin",
        "department": "Neurology",
        "clearance_level": 5,
    },
    {
        "id": "demo-neuro-001",
        "email": "neuro@neuropredict.sys",
        "password": "neuro123",
        "full_name": "Dr. James Wilson",
        "role": "neurologist",
        "department": "Neurology",
        "clearance_level": 4,
    },
    {
        "id": "demo-pharm-001",
        "email": "pharma@neuropredict.sys",
        "password": "pharma123",
        "full_name": "Dr. Priya Sharma",
        "role": "pharmacist",
        "department": "Pharmacy",
        "clearance_level": 3,
    },
    {
        "id": "demo-surg-001",
        "email": "surgery@neuropredict.sys",
        "password": "surgery123",
        "full_name": "Dr. Marcus Thompson",
        "role": "surgeon",
        "department": "Neurosurgery",
        "clearance_level": 4,
    },
    {
        "id": "demo-research-001",
        "email": "research@neuropredict.sys",
        "password": "research123",
        "full_name": "Dr. Elena Volkov",
        "role": "researcher",
        "department": "Research",
        "clearance_level": 3,
    },
    {
        "id": "demo-user-001",
        "email": "demo@neuropredict.sys",
        "password": "demo123",
        "full_name": "Demo User",
        "role": "demo",
        "department": None,
        "clearance_level": 1,
    },
]


def seed_demo_accounts():
    """Insert demo accounts into the database."""
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
