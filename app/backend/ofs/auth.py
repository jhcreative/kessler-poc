"""Logins for the five demo roles (plan §6, Q10): bcrypt and a signed session cookie.

What this defends against, and how:
- A stolen or guessed password: bcrypt (a deliberately slow hash), and a login rate limit per account and address,
  with a looser one per address so one address can't sweep many accounts.
- Telling which emails exist: an unknown email still runs one bcrypt check, and both failures read the same.
- Script reading the cookie: HttpOnly. A cookie sent over plain HTTP: Secure, unless COOKIE_SECURE=0 (local only).
- A request forged from another site: SameSite=Lax, plus an Origin check on every request that changes state.
- A login removed or disabled while its cookie lives: every request re-reads the account and the person.
- A forged cookie: HS256 with SESSION_SECRET, which lives only in the environment.

Accepted for the demo (Orly): no server-side session list, so logout clears the cookie rather than revoking it; the
cookie lasts 12 hours. Outbound email is off: there's no password reset, because ofs.com is a real domain.
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import SESSION
from .models import Person, Tech, User
from .states import Role

COOKIE = "ofs_session"
TTL_SECONDS = 12 * 3600
LOGIN_LIMIT = (10, 60.0)  # attempts per account and address, per window (seconds): guessing at one account
LOGIN_LIMIT_ADDRESS = (60, 60.0)  # attempts per address: one address sweeping many accounts
_DUMMY_HASH = bcrypt.hashpw(b"not-a-password", bcrypt.gensalt())


def _secret() -> str:
    secret = os.environ.get("SESSION_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("SESSION_SECRET is unset or shorter than 32 characters")
    return secret


def _secure() -> bool:
    return os.environ.get("COOKIE_SECURE", "1") != "0"


def allowed_origins() -> set[str]:
    return {o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:9219").split(",") if o.strip()}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


@dataclass(frozen=True)
class Caller:
    person: Person
    role: Role


class LoginIn(BaseModel):
    email: str
    password: str


class Me(BaseModel):
    person_id: uuid.UUID
    label: str
    role: Role
    email: str
    tech_id: uuid.UUID | None = None  # a tech's own id: the phone keeps to the jobs that carry it


async def _me(session: AsyncSession, person: Person, email: str) -> Me:
    tech_id = await session.scalar(select(Tech.id).where(Tech.person_id == person.id))
    return Me(person_id=person.id, label=person.label, role=Role(person.role), email=email, tech_id=tech_id)


_attempts: dict[str, deque[float]] = defaultdict(deque)


def _rate_limited(key: str, rule: tuple[int, float] = LOGIN_LIMIT) -> bool:
    limit, window = rule
    now = time.monotonic()
    q = _attempts[key]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(now)
    if len(_attempts) > 10_000:  # bounded memory: forget keys with nothing in the window (cold review, finding 14)
        for k in [k for k, d in _attempts.items() if not d or now - d[-1] > window]:
            del _attempts[k]
    return False


def check_origin(request: Request) -> None:
    """Refuse a state-changing request whose Origin is another site. No Origin (curl, tests) passes."""
    origin = request.headers.get("origin")
    if request.method not in ("GET", "HEAD", "OPTIONS") and origin and origin not in allowed_origins():
        raise HTTPException(403, "Cross-site request refused")


async def _person_for(session: AsyncSession, email: str) -> Person | None:
    user = await session.scalar(select(User).where(User.email == email, User.disabled.is_(False)))
    if user is None:
        return None
    return await session.scalar(select(Person).where(Person.email == email))


async def caller_for(session: AsyncSession, token: str | None) -> Caller | None:
    """The caller a session cookie names, or None: no cookie, a bad or expired one, or a login since removed."""
    if not token:
        return None
    try:
        claims = jwt.decode(token, _secret(), algorithms=["HS256"], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError:
        return None
    person = await _person_for(session, str(claims["sub"]))
    return Caller(person=person, role=Role(person.role)) if person else None


async def current(request: Request, session: AsyncSession = SESSION) -> Caller:
    caller = await caller_for(session, request.cookies.get(COOKIE))
    if caller is None:
        raise HTTPException(401, "Sign in first, or again: your session has ended")
    return caller


CURRENT = Depends(current)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Me)
async def login(body: LoginIn, request: Request, response: Response, session: AsyncSession = SESSION) -> Me:
    check_origin(request)
    email = body.email.strip().lower()
    address = request.client.host if request.client else "unknown"
    if _rate_limited(f"{address} {email}") or _rate_limited(address, LOGIN_LIMIT_ADDRESS):
        raise HTTPException(429, "Too many attempts; wait a minute")
    user = await session.scalar(select(User).where(User.email == email, User.disabled.is_(False)))
    # bcrypt reads 72 bytes at most and raises past that: check the first 72, then refuse anything longer, so a long
    # password is a 401 and takes the same time (cold review, finding 11). In a thread: it's slow by design, and
    # every open socket shares this event loop.
    password = body.password.encode()
    stored = user.password_hash.encode() if user else _DUMMY_HASH
    ok = await asyncio.to_thread(bcrypt.checkpw, password[:72], stored) and len(password) <= 72
    person = await _person_for(session, email) if user and ok else None
    if person is None:
        raise HTTPException(401, "That email and password don't match")
    token = jwt.encode({"sub": email, "exp": int(time.time()) + TTL_SECONDS}, _secret(), algorithm="HS256")
    response.set_cookie(COOKIE, token, max_age=TTL_SECONDS, httponly=True, secure=_secure(), samesite="lax", path="/")
    return await _me(session, person, email)


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response) -> None:
    check_origin(request)
    response.delete_cookie(COOKIE, path="/", httponly=True, secure=_secure(), samesite="lax")


@router.get("/me", response_model=Me)
async def me(caller: Caller = CURRENT, session: AsyncSession = SESSION) -> Me:
    return await _me(session, caller.person, caller.person.email or "")
