from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt, JWTError
import os
import json
from pathlib import Path

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import User, Token, TokenData
from app.core.config import settings

# Allow OAuth over HTTP in development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

router = APIRouter()

# Google OAuth scopes
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Initialize OAuth flow
flow = Flow.from_client_secrets_file(
    settings.CLIENT_SECRET_PATH,
    scopes=SCOPES,
    redirect_uri="http://localhost:8000/api/v1/auth/callback",
)

# Get client_id from client secrets file
with open(settings.CLIENT_SECRET_PATH) as f:
    client_config = json.load(f)
    CLIENT_ID = client_config["web"]["client_id"]


@router.get("/login")
async def login():
    """Start OAuth flow by redirecting to Google's consent screen"""
    authorization_url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )
    return RedirectResponse(authorization_url)


@router.get("/callback")
async def callback(request: Request, response: Response, db: Session = Depends(get_db)):
    """Handle callback from Google after user has granted permission"""
    try:
        flow.fetch_token(authorization_response=str(request.url))
        credentials = flow.credentials

        # Get user info from Google
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, google_requests.Request(), CLIENT_ID
        )

        # Extract user info
        email = id_info.get("email")
        google_id = id_info.get("sub")
        full_name = id_info.get("name")

        if not all([email, google_id, full_name]):
            raise HTTPException(
                status_code=400,
                detail="Required user information missing from Google response",
            )

        # Get or create user
        auth_service = AuthService(db)
        user = auth_service.get_user_by_google_id(google_id)

        if not user:
            user = auth_service.create_user(
                email=email, google_id=google_id, full_name=full_name
            )

        # Save credentials
        auth_service.save_user_credentials(
            user.id, credentials.token, credentials.refresh_token, credentials.expiry
        )

        # Create access token
        access_token, expires_at = auth_service.create_access_token(user.id)

        # Set cookie and redirect
        response = RedirectResponse(url="/job-registry")
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax",
        )

        return response

    except Exception as e:
        print(f"Error in callback: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Failed to process Google callback: {str(e)}"
        )


@router.get("/user/me", response_model=User)
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current logged in user from JWT token"""
    try:
        token = request.cookies.get("access_token")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")

        token = token.split(" ")[1]
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        auth_service = AuthService(db)
        user = auth_service.get_user_by_id(int(user_id))
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return User(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            google_id=user.google_id,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
