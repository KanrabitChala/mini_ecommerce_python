
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    TokenResponse,
)
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    username = data.username
    email = str(data.email).strip().lower()

    existing = db.query(User).filter(
        or_(User.username == username, User.email == email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Username or email already registered",
        )

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(data.password),
        is_admin=False,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Username or email already registered",
        )

    return user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    username = data.username.strip()

    user = db.query(User).filter(User.username == username).first()

    if user is None or not verify_password(
        data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user
