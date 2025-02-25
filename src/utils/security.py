from typing import Optional
import jwt
import secrets
from datetime import datetime, timedelta
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# Generates a 64 byte (512 bit) URL-safe secret key
SECRET_KEY = secrets.token_urlsafe(64)


def encrypt_password(password: str):
    return generate_password_hash(password)


def check_password(hash: str, password: str):
    return check_password_hash(hash, password)


def generate_jwt_token(id: int, pwd: str) -> str:
    payload = {
        "exp": datetime.utcnow() + timedelta(hours=6),  # Token expires in 6 hours
        "iat": datetime.utcnow(),
        "sub": id,
        "pwd": pwd
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_jwt_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token
