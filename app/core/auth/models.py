from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    google_id = Column(String, unique=True, index=True)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relation till UserCredentials
    credentials = relationship("UserCredentials", back_populates="user", uselist=False)


class UserCredentials(Base):
    __tablename__ = "user_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    token = Column(String)  # Krypterad access token
    refresh_token = Column(String)  # Krypterad refresh token
    token_expiry = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relation till User
    user = relationship("User", back_populates="credentials")
