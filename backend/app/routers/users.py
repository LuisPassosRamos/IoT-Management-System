from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.db_models import User, UserRole, Resource, ResourcePermission
from app.models.schemas import UserSummary, UserCreate, UserUpdate, PermissionUpdateRequest
from app.services.auth import require_admin, require_active_user, get_password_hash

router = APIRouter()


def _user_to_schema(user: User) -> UserSummary:
    return UserSummary(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        permitted_resource_ids=[perm.resource_id for perm in user.permissions],
    )


@router.get("/users/me", response_model=UserSummary)
async def get_me(current_user: User = Depends(require_active_user)) -> UserSummary:
    return _user_to_schema(current_user)


@router.get("/users", response_model=List[UserSummary])
async def list_users(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> List[UserSummary]:
    users = db.scalars(
        select(User)
        .options(selectinload(User.permissions))
        .order_by(User.username)
    ).unique().all()
    return [_user_to_schema(user) for user in users]


@router.post("/users", response_model=UserSummary, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserSummary:
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=400, detail="Username already exists")
    if payload.email and db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        role=UserRole(payload.role),
        is_active=payload.is_active,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    db.flush()

    if payload.allowed_resource_ids:
        _sync_permissions(db, user, payload.allowed_resource_ids)

    db.refresh(user)
    return _user_to_schema(user)


@router.put("/users/{user_id}", response_model=UserSummary)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserSummary:
    user = db.scalar(
        select(User)
        .options(selectinload(User.permissions))
        .where(User.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = payload.model_dump(exclude_unset=True)

    if "role" in updates and updates["role"] is not None:
        user.role = UserRole(updates.pop("role"))
    if "password" in updates and updates["password"]:
        user.password_hash = get_password_hash(updates.pop("password"))

    allowed_ids = updates.pop("allowed_resource_ids", None)

    for attr, value in updates.items():
        setattr(user, attr, value)

    if allowed_ids is not None:
        _sync_permissions(db, user, allowed_ids)

    db.flush()
    db.refresh(user)
    return _user_to_schema(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)


@router.put("/users/{user_id}/permissions", response_model=UserSummary)
async def update_permissions(
    user_id: int,
    request: PermissionUpdateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserSummary:
    user = db.scalar(
        select(User)
        .options(selectinload(User.permissions))
        .where(User.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    _sync_permissions(db, user, request.resource_ids)
    db.flush()
    db.refresh(user)
    return _user_to_schema(user)


def _sync_permissions(db: Session, user: User, resource_ids: List[int]) -> None:
    existing_ids = {perm.resource_id for perm in user.permissions}
    target_ids = set(resource_ids)

    # Remove old permissions
    for perm in list(user.permissions):
        if perm.resource_id not in target_ids:
            db.delete(perm)

    # Add new ones
    for resource_id in target_ids - existing_ids:
        if not db.get(Resource, resource_id):
            continue
        db.add(ResourcePermission(user_id=user.id, resource_id=resource_id))
