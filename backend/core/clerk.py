"""
NEURO_PREDICT_SYS — Clerk Integration
Verifies Clerk session JWTs and handles webhooks.
"""
import hashlib
import hmac
import json
from typing import Optional
from fastapi import Request, HTTPException
from .config import get_settings

settings = get_settings()


async def verify_clerk_token(token: str) -> dict:
    """
    Verify a Clerk session JWT.
    In production, use clerk_backend_api or jwk-based verification.
    For demo mode, decode the JWT payload without verification.
    """
    if not settings.CLERK_SECRET_KEY:
        # Demo mode — accept any token structure
        try:
            import base64
            parts = token.split(".")
            if len(parts) >= 2:
                payload = parts[1]
                # Add padding
                payload += "=" * (4 - len(payload) % 4)
                data = json.loads(base64.urlsafe_b64decode(payload))
                return {
                    "sub": data.get("sub", "demo-user"),
                    "email": data.get("email", "demo@neuropredict.sys"),
                    "role": data.get("role", "user"),
                }
        except Exception:
            pass
        # Fallback for non-JWT tokens
        return {"sub": "demo-user", "email": "demo@neuropredict.sys", "role": "user"}

    # Production: verify with Clerk's JWK endpoint
    try:
        from jose import jwt
        # Fetch Clerk's JWK set (cached)
        import httpx
        jwks_url = f"https://api.clerk.com/v1/jwks"
        async with httpx.AsyncClient() as client:
            resp = await client.get(jwks_url, headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"})
            jwks = resp.json()

        # Find the right key
        header = jwt.get_unverified_header(token)
        key_id = header.get("kid")
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == key_id:
                from jose import jwt as jose_jwt
                payload = jose_jwt.decode(
                    token,
                    jwk,
                    algorithms=["RS256"],
                    options={"verify_aud": False},
                )
                return {
                    "sub": payload.get("sub", ""),
                    "email": payload.get("email", ""),
                    "role": payload.get("role", "user"),
                    "metadata": payload.get("metadata", {}),
                }
        raise HTTPException(status_code=401, detail="Invalid Clerk token")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


def verify_clerk_webhook签名(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Clerk webhook signature (svix)."""
    if not secret:
        return True  # Demo mode
    try:
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


async def get_clerk_user(request: Request) -> dict:
    """Extract user from Clerk session in request."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return await verify_clerk_token(token)

    # Check for Clerk session cookie
    session_token = request.cookies.get("__session")
    if session_token:
        return await verify_clerk_token(session_token)

    return None
