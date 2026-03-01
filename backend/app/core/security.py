from datetime import datetime, timedelta, timezone
from typing import Any, Union
import asyncio
from functools import partial
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Synchronous helpers (use only in threads, never on event loop) ──────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Synchronous bcrypt verify — always call the async version from routes."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Synchronous bcrypt hash — always call the async version from routes."""
    return pwd_context.hash(password)

# ── Async wrappers (offload CPU-bound bcrypt to thread pool) ─────────────────

async def async_verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Async bcrypt verify — runs in a thread pool so it never blocks the event loop.
    Use this in all async route handlers instead of verify_password().
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, partial(pwd_context.verify, plain_password, hashed_password)
    )

async def async_get_password_hash(password: str) -> str:
    """
    Async bcrypt hash — runs in a thread pool so it never blocks the event loop.
    Use this in all async route handlers instead of get_password_hash().
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(pwd_context.hash, password))

# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(data: dict[str, Any], expires_delta: Union[timedelta, None] = None) -> str:
    """
    Creates a signed HS256 JWT.  The 'email' and 'role' claims are expected
    in *data*; an 'exp' claim is added automatically.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
