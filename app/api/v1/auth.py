from datetime import timedelta
from typing import Any, Dict, Optional
import httpx
import os
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.core.db import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.services.user_service import (
    get_user_by_email,
    get_user_by_google_id,
    create_user,
)
from app.schemas.user import UserCreate

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


def create_flow():
    """
    Create a Google OAuth flow instance
    """
    client_secret_path = Path(settings.CLIENT_SECRET_PATH)
    if not client_secret_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Client secret file not found",
        )

    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow
    flow = Flow.from_client_secrets_file(
        client_secret_path,
        scopes=SCOPES,
        redirect_uri=f"http://localhost:8000/api/v1/auth/callback",
    )

    return flow


@router.get("/google")
async def login_google():
    """
    Redirect to Google OAuth login
    """
    try:
        # Create flow
        flow = create_flow()

        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
        )

        # Store state for CSRF protection
        # In a real app, you'd store this in a session or cookie
        # For simplicity, we'll use a query parameter
        return RedirectResponse(url=authorization_url)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating authorization URL: {str(e)}",
        )


@router.get("/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Google OAuth callback
    """
    # Get authorization code from query parameters
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided",
        )

    try:
        # Create flow
        flow = create_flow()

        # Exchange authorization code for credentials
        flow.fetch_token(code=code)

        # Get credentials
        credentials = flow.credentials

        # Get user info from Google
        service = build("oauth2", "v2", credentials=credentials)
        userinfo = service.userinfo().get().execute()

        # Check if user exists
        user = get_user_by_google_id(db, userinfo["id"])

        if not user:
            # Create new user
            user_in = UserCreate(
                email=userinfo["email"],
                full_name=userinfo.get("name"),
                google_id=userinfo["id"],
            )
            user = create_user(db, user_in)

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(user.id, expires_delta=access_token_expires)

        # Redirect to frontend with token
        return RedirectResponse(url=f"/?token={token}&user_id={user.id}")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in OAuth callback: {str(e)}",
        )
