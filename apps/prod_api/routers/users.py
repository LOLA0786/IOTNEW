from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import hashlib, os, uuid
from apps.prod_api.db_models import SessionLocal, Portfolio, Trade
from apps.prod_api.auth import create_jwt

router = APIRouter(prefix="/users", tags=["Users"])


class SignupReq(BaseModel):
    username: str
    password: str


class LoginReq(BaseModel):
    username: str
    password: str


# Simple file-based user store (replace with proper DB in production)
USERS_FILE = "./users.json"


def _load_users():
    import json

    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(d):
    import json

    with open(USERS_FILE, "w") as f:
        json.dump(d, f, indent=2)


@router.post("/signup")
def signup(req: SignupReq):
    u = _load_users()
    if req.username in u:
        raise HTTPException(400, "exists")
    salt = uuid.uuid4().hex
    pwdhash = hashlib.sha256((req.password + salt).encode()).hexdigest()
    api_key = uuid.uuid4().hex
    u[req.username] = {"pwd": pwdhash, "salt": salt, "api_key": api_key}
    _save_users(u)
    token = create_jwt(req.username)
    return {"username": req.username, "api_key": api_key, "token": token}


@router.post("/login")
def login(req: LoginReq):
    u = _load_users()
    if req.username not in u:
        raise HTTPException(400, "invalid")
    rec = u[req.username]
    h = hashlib.sha256((req.password + rec["salt"]).encode()).hexdigest()
    if h != rec["pwd"]:
        raise HTTPException(400, "invalid")
    token = create_jwt(req.username)
    return {"username": req.username, "api_key": rec["api_key"], "token": token}
