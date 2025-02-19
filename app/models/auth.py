from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class AuthUser(Base):
    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    google_id = Column(String, unique=True, index=True)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    credentials = relationship("AuthUserCredentials", back_populates="auth_user", uselist=False)
    jobs = relationship("Job", back_populates="auth_user")

class AuthUserCredentials(Base):
    __tablename__ = "auth_user_credentials"

    id = Column(Integer, primary_key=True, index=True)
    auth_user_id = Column(Integer, ForeignKey("auth_users.id"), unique=True)
    token = Column(String)  # Krypterad access token
    refresh_token = Column(String)  # Krypterad refresh token
    token_expiry = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relation till AuthUser
    auth_user = relationship("AuthUser", back_populates="credentials")