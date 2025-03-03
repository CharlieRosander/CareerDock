from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.sql import func
from app.core.db import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid


class JobAd(Base):
    __tablename__ = "job_ads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(String, nullable=True)
    job_url = Column(String, nullable=True)
    category = Column(String, nullable=True)
    date_posted = Column(DateTime(timezone=True), server_default=func.now())
    keywords = Column(String, nullable=True)