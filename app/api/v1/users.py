from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.db import get_db
from app.core.auth import get_current_user
from app.schemas.user import User, UserUpdate
from app.services.user_service import (
    get_user_by_id,
    get_users,
    update_user,
)

router = APIRouter()

@router.get("/me", response_model=User)
async def read_users_me(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Get current user.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

@router.get("/", response_model=List[User])
async def read_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve users.
    """
    # Check if user is superuser to allow listing all users
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to list all users",
        )
    
    users = get_users(db, skip=skip, limit=limit)
    return users

@router.put("/{user_id}", response_model=User)
async def update_existing_user(
    request: Request,
    user_id: UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a user.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this ID does not exist in the system",
        )
    
    # Check if user is updating their own profile or is a superuser
    if str(current_user.id) != str(user_id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user",
        )
    
    user = update_user(db, user, user_in)
    return user
