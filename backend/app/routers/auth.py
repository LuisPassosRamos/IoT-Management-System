from datetime import timedelta
from fastapi import APIRouter, HTTPException
from app.models.schemas import LoginRequest, LoginResponse
from app.services.auth import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """User authentication endpoint."""
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=401, detail="Invalid username or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "role": user["role"],
            "user_id": user["id"],
        },
        expires_delta=access_token_expires,
    )

    return LoginResponse(
        token=access_token,
        role=user["role"],
        username=user["username"],
        user_id=user["id"],
    )
