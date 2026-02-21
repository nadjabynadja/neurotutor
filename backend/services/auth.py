import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


class AuthService:
    """Authentication service for user management."""

    @staticmethod
    def hash_password(password: str) -> str:
        return get_password_hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)

    @staticmethod
    def create_token(user_id: int, email: str) -> str:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(
            data={"sub": str(user_id), "email": email},
            expires_delta=access_token_expires
        )

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        return decode_access_token(token)
