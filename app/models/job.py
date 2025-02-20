from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Numeric,
    Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_users.id"))

    # Basic info
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    description = Column(Text)
    location = Column(String(255))
    job_type = Column(String(50))  # Full-time, Part-time, Contract, etc.
    industry = Column(String(100))  # Tech, Finance, Healthcare, etc.

    # Application details
    status = Column(String(50), nullable=False)
    application_date = Column(DateTime, nullable=False)
    application_method = Column(String(50))  # Email, Website, LinkedIn, etc.
    application_url = Column(String(512))
    salary_min = Column(Numeric(10, 2))
    salary_max = Column(Numeric(10, 2))
    salary_currency = Column(String(3), default="SEK")  # ISO 4217 currency code

    # Contact info
    contact_name = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))

    # Follow-up
    next_follow_up = Column(DateTime)
    last_response_date = Column(DateTime)
    interview_date = Column(DateTime)
    notes = Column(Text)

    # AI-related fields
    ai_parsed = Column(Boolean, default=False)  # Whether the job was parsed by AI
    ai_confidence = Column(Numeric(3, 2))  # Confidence score of AI parsing (0-1)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    auth_user = relationship(
        "AuthUser", back_populates="jobs"
    )  # Ändrat från user till auth_user
