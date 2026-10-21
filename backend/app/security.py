import hashlib, secrets
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.config import settings

ph = PasswordHasher()

def hash_password(pw:str) -> str:
    return ph.hash(pw)

def verify_password(pw:str, hashed:str) -> bool:
    try:
        return ph.verify(hashed, pw)
    except VerifyMismatchError:
        return False

def create_access_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(
        minutes = settings.ACCESS_TOKEN_MINUTES
    )

    data = {
        "sub" : user_id,
        "exp" : exp,
        "type" : "access"
    }
    return jwt.encode(
        data, settings.JWT_SECRET, 
        algorithm = settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> dict:
    return jwt.decode(
        token, 
        settings.JWT_SECRET,
        algorithms = [settings.JWT_ALGORITHM]
    )

def new_refresh_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(48)
    hashed = hashlib.sha256(raw.encode()).hexdigest()

    return raw, hashed

def hash_refresh(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()