
import os
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from itsdangerous import URLSafeTimedSerializer
from itsdangerous.exc import BadSignature, SignatureExpired
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from database import get_db
from models import User

password_hasher = PasswordHash.recommended()

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
if not SECRET_KEY:
    # Local development only; configure a stable secret before deployment.
    SECRET_KEY = secrets.token_hex(32)

serializer = URLSafeTimedSerializer(
    SECRET_KEY,
    salt="mini-ecommerce-auth",
)

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hasher.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    return serializer.dumps({"sub": str(user_id)})


def verify_access_token(token: str) -> int | None:
    try:
        payload = serializer.loads(token, max_age=3600)
        return int(payload["sub"])
    except (BadSignature, SignatureExpired, ValueError, TypeError, KeyError):
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = verify_access_token(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Administrator access required",
        )

    return current_user
