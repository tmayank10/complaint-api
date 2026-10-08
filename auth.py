"""Password hashing and login tokens.

Tokens are signed so the server can check them without storing a session.
A wrong or missing token gets 401.
"""

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

SECRET = os.environ.get("COMPLAINT_SECRET", "dev-secret-change-me")
ALGO = "HS256"
TOKEN_HOURS = 12


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return "%s$%s" % (salt, digest.hex())


def verify_password(password, stored):
    try:
        salt, _digest = stored.split("$", 1)
    except ValueError:
        return False
    check = hash_password(password, salt)
    return hmac.compare_digest(check, stored)


def make_token(user_id, username):
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def read_token(token):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
