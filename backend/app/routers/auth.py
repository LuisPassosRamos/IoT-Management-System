from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.schemas import LoginRequest, LoginResponse
from app.services.auth import authenticate_user, create_access_token

router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest, db: Session = Depends(get_db)
) -> LoginResponse:
    """Authenticate a user and return a JWT token."""

    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value,
            "user_id": user.id,
        },
        expires_delta=access_token_expires,
    )

    return LoginResponse(
        token=access_token,
        role=user.role.value,
        username=user.username,
        user_id=user.id,
        full_name=user.full_name,
    )
