from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta

# OBS - Tillåt OAuth över HTTP i utveckling
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from app.database import get_db
from app.crud.user import get_user_by_google_id, create_user, get_user_by_email
from app.crud.credentials import save_user_credentials

# Ladda miljövariabler
load_dotenv()

# Hämta konfiguration från miljövariabler
CLIENT_CONFIG_PATH = Path(os.getenv("CLIENT_SECRET_PATH"))

# Google OAuth-scopes
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.modify",
]

# JWT-inställningar
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # Byt ut i produktion!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

router = APIRouter()


def create_access_token(data: dict):
    """Skapa en JWT token för användaren"""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Läs in OAuth config
with open(CLIENT_CONFIG_PATH) as f:
    client_config = json.load(f)

# Konfigurera OAuth flow
flow = Flow.from_client_config(
    client_config,
    scopes=SCOPES,
    redirect_uri="http://localhost:8000/auth/callback",
)


@router.get("/login")
async def login():
    """Starta OAuth-flödet genom att redirecta till Google's consent screen"""
    authorization_url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )
    return RedirectResponse(authorization_url)


@router.get("/callback")
async def callback(request: Request, response: Response, db: Session = Depends(get_db)):
    """Hantera callback från Google efter att användaren har godkänt"""
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials

    try:
        # Hämta användarinfo från ID token
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, requests.Request(), client_config["web"]["client_id"]
        )

        # Kolla om användaren redan finns
        user = get_user_by_google_id(db, id_info["sub"])

        if not user:
            # Skapa ny användare
            user = create_user(
                db,
                google_id=id_info["sub"],
                email=id_info["email"],
                full_name=id_info.get("name", ""),
            )

        # Spara Gmail credentials
        token_expiry = datetime.fromtimestamp(credentials.expiry.timestamp())
        save_user_credentials(
            db=db,
            user_id=user.id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token
            or "",  # Kan vara None första gången
            token_expiry=token_expiry,
        )

        # Skapa JWT token för användaren
        access_token = create_access_token(
            data={
                "sub": user.email,
                "google_id": user.google_id,
            }
        )

        # Sätt token som cookie
        response = RedirectResponse(url="/dashboard")
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,  # Sätt till True i produktion (HTTPS)
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Hämta nuvarande inloggad användare från JWT token"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception

    return user
