from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from jose import jwt
from cryptography.fernet import Fernet

from app.core.config import settings
from app.models.auth import AuthUser, AuthUserCredentials


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        if settings.ENCRYPTION_KEY:
            self.cipher_suite = Fernet(settings.ENCRYPTION_KEY.encode())

    def get_user_by_id(self, user_id: int) -> Optional[AuthUser]:
        """Get user by ID"""
        return self.db.query(AuthUser).filter(AuthUser.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        """Get user by email"""
        return self.db.query(AuthUser).filter(AuthUser.email == email).first()

    def get_user_by_google_id(self, google_id: str) -> Optional[AuthUser]:
        """Get user by Google ID"""
        return self.db.query(AuthUser).filter(AuthUser.google_id == google_id).first()

    def create_user(self, email: str, google_id: str, full_name: str) -> AuthUser:
        """Create a new user"""
        user = AuthUser(
            email=email,
            google_id=google_id,
            full_name=full_name,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def encrypt_token(self, token: str) -> str:
        """Encrypt a token using Fernet encryption"""
        if not settings.ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY must be set")
        return self.cipher_suite.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token using Fernet encryption"""
        if not settings.ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY must be set")
        return self.cipher_suite.decrypt(encrypted_token.encode()).decode()

    def save_user_credentials(
        self,
        user_id: int,
        access_token: str,
        refresh_token: str,
        token_expiry: datetime,
    ) -> AuthUserCredentials:
        """Save or update user's OAuth credentials"""
        credentials = (
            self.db.query(AuthUserCredentials)
            .filter(AuthUserCredentials.auth_user_id == user_id)
            .first()
        )

        if not credentials:
            credentials = AuthUserCredentials(
                auth_user_id=user_id,
                token=self.encrypt_token(access_token),
                refresh_token=(
                    self.encrypt_token(refresh_token) if refresh_token else None
                ),
                token_expiry=token_expiry,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.db.add(credentials)
        else:
            credentials.token = self.encrypt_token(access_token)
            if refresh_token:
                credentials.refresh_token = self.encrypt_token(refresh_token)
            credentials.token_expiry = token_expiry
            credentials.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(credentials)
        return credentials

    def get_user_credentials(self, user_id: int) -> Optional[dict]:
        """Get user's OAuth credentials"""
        credentials = (
            self.db.query(AuthUserCredentials)
            .filter(AuthUserCredentials.auth_user_id == user_id)
            .first()
        )

        if not credentials:
            return None

        return {
            "token": self.decrypt_token(credentials.token),
            "refresh_token": (
                self.decrypt_token(credentials.refresh_token)
                if credentials.refresh_token
                else None
            ),
            "token_expiry": credentials.token_expiry,
        }

    def create_access_token(self, user_id: int) -> Tuple[str, datetime]:
        """Skapa JWT access token och returnera token samt utgångstid"""
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now() + expires_delta

        to_encode = {"sub": str(user_id), "exp": expire}

        token = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        
        return token, expire
