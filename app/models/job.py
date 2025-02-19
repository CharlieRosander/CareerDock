from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("auth_users.id")
    )  # Updated to match new auth table
    title = Column(String, index=True)
    company = Column(String, index=True)
    description = Column(Text, nullable=True)
    status = Column(String)  # applied, interviewing, offered, rejected
    application_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    auth_user = relationship("AuthUser", back_populates="jobs")
