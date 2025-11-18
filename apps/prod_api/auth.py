import os, datetime
from typing import Optional
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
import jwt

API_KEY_HEADER = APIKeyHeader(name="X-API-KEY", auto_error=False)
bearer = HTTPBearer(auto_error=False)
SECRET = os.getenv("SECRET_KEY", "change-me")


def verify_api_key(key: str) -> Optional[dict]:
    # Placeholder: you can map API keys to users in DB
    # For demo: accept any non-empty key and return a simple payload
    if not key:
        return None
    return {"sub": key, "role": "user"}


async def get_current_user_api(key: str = Depends(API_KEY_HEADER)):
    if key:
        u = verify_api_key(key)
        if u:
            return u
    raise HTTPException(status_code=401, detail="Invalid API Key")


# JWT helpers for user login sessions
def create_jwt(subject: str, hours: int = 24):
    payload = {
        "sub": subject,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=hours),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def decode_jwt(token: str):
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        return None


async def get_current_user_jwt(creds: HTTPAuthorizationCredentials = Security(bearer)):
    if not creds:
        raise HTTPException(status_code=401, detail="Missing auth token")
    payload = decode_jwt(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload
