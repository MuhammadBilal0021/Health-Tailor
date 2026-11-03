import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session as DBSession
from database import get_db
from models import User, Session, RateBucket
import os

COOKIE = "ht_session"


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return salt.hex() + ":" + digest.hex()


def verify_password(password, stored):
    try:
        salt, expected = stored.split(":")
        return hmac.compare_digest(
            hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex(),
            expected,
        )
    except (ValueError, TypeError):
        return False


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def issue_session(db, user, response):
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    db.add(
        Session(
            token_hash=digest(token),
            user_id=user.id,
            csrf=csrf,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
    )
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "true") == "true",
        samesite="lax",
        max_age=604800,
        path="/",
    )
    return csrf


def current_user(request: Request, db: DBSession = Depends(get_db)):
    token = request.cookies.get(COOKIE)
    record = db.get(Session, digest(token)) if token else None
    if not record or record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(401, "Please sign in.")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if not hmac.compare_digest(request.headers.get("X-CSRF-Token", ""), record.csrf):
            raise HTTPException(403, "Session verification failed. Reload and retry.")
    user = db.get(User, record.user_id)
    if not user:
        raise HTTPException(401, "Account not found.")
    request.state.session_record = record
    return user


def require_role(user, *roles):
    if user.role not in roles:
        raise HTTPException(403, "This action is not allowed for your account.")


def rate_limit(db, identity, limit=10, seconds=900):
    # Each window has a deterministic key. Upserts serialize increments in PostgreSQL.
    window = int(time.time()) // seconds
    key = digest(f"{identity}:{window}")
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    statement = insert(RateBucket).values(key=key, count=1, window=window)
    statement = statement.on_conflict_do_update(
        index_elements=["key"], set_={"count": RateBucket.count + 1}
    ).returning(RateBucket.count)
    count = db.execute(statement).scalar_one()
    db.commit()  # Persist unsuccessful attempts too; call before other mutations.
    if count > limit:
        raise HTTPException(429, "Too many attempts. Please try again later.")
