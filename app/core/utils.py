import jwt
from datetime import datetime, timedelta, timezone

from .config import password_context, get_settings


def generate_password_hash(plain_password: str) -> str:
    return password_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)


def create_jwt_token(data: dict, secret_key: str, expires_in: int) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=expires_in)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=get_settings().jwt_algorithm)


def verify_jwt_token(token: str, secret_key: str) -> dict:
    try:
        return jwt.decode(token, secret_key, algorithms=[get_settings().jwt_algorithm])
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}
