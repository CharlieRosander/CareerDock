from datetime import timedelta
from typing import Optional
import os
import logging
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
            detail="Client secret file not found",
        )

    flow = Flow.from_client_secrets_file(
        client_secret_path,
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )

    return flow


@router.get("/google")
async def login_google():
    """
    Redirect to Google OAuth login
    """
    try:
        flow = create_flow()
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
        )
        return RedirectResponse(url=authorization_url)

    except Exception as e:
        logging.error(f"Error creating authorization URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating authorization URL",
        )


@router.get("/callback")
async def google_callback(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Google OAuth callback
    """
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided",
        )

    try:
        flow = create_flow()
        flow.fetch_token(code=code)
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

        # Create redirect and set token in cookie
        # Using status_code=303 (See Other) to force a GET request and full page refresh
        redirect_response = RedirectResponse(url="/dashboard", status_code=303)
        
        redirect_response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
            path="/",
        )

        return redirect_response

    except Exception as e:
        logging.error(f"Error in OAuth callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error occurred",
        )


@router.get("/logout")
async def logout():
    """
    Logout user by clearing the access token cookie
    """
    # Using status_code=303 (See Other) to force a GET request and full page refresh
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token", path="/")
    
    # Add debug logging
    logging.debug("User logged out, access_token cookie cleared")
    
    return response
