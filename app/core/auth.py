from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from uuid import UUID
import logging
from typing import Optional

from .config import settings
from .db import get_db
from .security import ALGORITHM, decode_access_token
from app.services.user_service import get_user_by_id


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(self, tokenUrl: str, auto_error: bool = True):
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": {}})
        super().__init__(flows=flows, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        # Try to get token from Authorization header first
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization.replace("Bearer ", "")
        
        # Try to get token from cookie - expecting token directly without Bearer prefix
        cookie_authorization = request.cookies.get("access_token")
        if cookie_authorization:
            return cookie_authorization
        
        # No token found
        if self.auto_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearerWithCookie(
    tokenUrl=f"{settings.API_V1_STR}/auth/google", auto_error=False
)


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
):
    """
    Get the current user from the JWT token
    """
    logger = logging.getLogger(__name__)
    
    # If no token from oauth2_scheme, try to get directly from cookies
    if not token:
        logger.debug("No token from oauth2_scheme, trying cookies directly")
        token = request.cookies.get("access_token")
    
    if not token:
        logger.debug("No token provided")
        return None

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Try to decode token to get user ID
        user_id = decode_access_token(token)
        if user_id is None:
            logger.warning("No user_id in token")
            raise credentials_exception
    except Exception as e:
        logger.error(f"Exception decoding token: {str(e)}")
        raise credentials_exception

    # Get user from database
    try:
        user = get_user_by_id(db, UUID(user_id))
        if user is None:
            logger.warning(f"No user found with id {user_id}")
            raise credentials_exception
        
        # Store user in request.state for easy access in other parts of the app
        request.state.user = user
        return user
    except ValueError as e:
        logger.error(f"ValueError when getting user: {str(e)}")
        raise credentials_exception
