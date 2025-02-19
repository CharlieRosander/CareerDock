from sqlalchemy.orm import Session
from app.core.auth.models import UserCredentials
from datetime import datetime
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

# Ladda krypteringsnyckel från miljövariabler
load_dotenv()
ENCRYPTION_KEY = os.getenv("CREDENTIALS_ENCRYPTION_KEY", Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_token(token: str) -> str:
    """Krypterar en token"""
    return cipher_suite.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Dekrypterar en token"""
    return cipher_suite.decrypt(encrypted_token.encode()).decode()

def save_user_credentials(
    db: Session,
    user_id: int,
    access_token: str,
    refresh_token: str,
    token_expiry: datetime
):
    """Sparar eller uppdaterar användarens credentials"""
    # Kryptera tokens innan de sparas
    encrypted_access_token = encrypt_token(access_token)
    encrypted_refresh_token = encrypt_token(refresh_token)

    # Kolla om credentials redan finns
    credentials = db.query(UserCredentials).filter(
        UserCredentials.user_id == user_id
    ).first()

    if credentials:
        # Uppdatera existerande credentials
        credentials.token = encrypted_access_token
        credentials.refresh_token = encrypted_refresh_token
        credentials.token_expiry = token_expiry
    else:
        # Skapa nya credentials
        credentials = UserCredentials(
            user_id=user_id,
            token=encrypted_access_token,
            refresh_token=encrypted_refresh_token,
            token_expiry=token_expiry
        )
        db.add(credentials)

    db.commit()
    db.refresh(credentials)
    return credentials

def get_user_credentials(db: Session, user_id: int):
    """Hämtar användarens credentials"""
    credentials = db.query(UserCredentials).filter(
        UserCredentials.user_id == user_id
    ).first()

    if not credentials:
        return None

    # Dekryptera tokens innan de returneras
    return {
        "access_token": decrypt_token(credentials.token),
        "refresh_token": decrypt_token(credentials.refresh_token),
        "token_expiry": credentials.token_expiry
    }
