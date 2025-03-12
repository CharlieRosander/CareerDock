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
        
        # Try to get token from cookie - now expecting token directly without Bearer prefix
        cookie_authorization = request.cookies.get("access_token")
        if cookie_authorization:
            # Return the token as is, no need to remove Bearer prefix
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
    # Använd strukturerad loggning istället för print-satser
    logger = logging.getLogger(__name__)
    
    # Om ingen token från oauth2_scheme, försök hämta direkt från cookies
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
        # Försök dekoda token för att få användar-ID
        user_id = decode_access_token(token)
        if user_id is None:
            logger.warning("No user_id in token")
            raise credentials_exception
    except Exception as e:
        logger.error(f"Exception decoding token: {str(e)}")
        raise credentials_exception

    # Hämta användare från databasen
    try:
        user = get_user_by_id(db, UUID(user_id))
        if user is None:
            logger.warning(f"No user found with id {user_id}")
            raise credentials_exception
        
        # Spara användaren i request.state för enkel åtkomst i andra delar av appen
        request.state.user = user
        return user
    except ValueError as e:
        logger.error(f"ValueError when getting user: {str(e)}")
        raise credentials_exception
