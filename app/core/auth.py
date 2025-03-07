from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from .config import settings
from .db import get_db
from .security import ALGORITHM, decode_access_token
from app.services.user_service import get_user_by_id

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/google", auto_error=False
)


async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    """
    Get the current user from the JWT token
    """
    print(f"Token received: {token}")
    if not token:
        print("No token provided")
        return None

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_access_token(token)
        print(f"Decoded user_id: {user_id}")
        if user_id is None:
            print("No user_id in token")
            raise credentials_exception
    except Exception as e:
        print(f"Exception decoding token: {str(e)}")
        raise credentials_exception

    # Get user from database
    try:
        user = get_user_by_id(db, UUID(user_id))
        print(f"User from DB: {user}")
        if user is None:
            print(f"No user found with id {user_id}")
            raise credentials_exception
        return user
    except ValueError as e:
        print(f"ValueError: {str(e)}")
        raise credentials_exception
