from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.types import TypeDecorator, DateTime as SQLDateTime
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime, timezone
import uuid


class UTCDateTime(TypeDecorator):
    """Custom SQLAlchemy type that ensures all datetimes are stored as UTC"""

    impl = SQLDateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
            return value.replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return value.replace(tzinfo=timezone.utc)
        return value


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    github_username = Column(String, nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(UTCDateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        UTCDateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login = Column(UTCDateTime, nullable=True)
    
    # Relationships
    repositories = relationship("Repository", back_populates="user")
    project_analyses = relationship("ProjectAnalysis", back_populates="user")
    linkedin_profiles = relationship("LinkedInProfile", back_populates="user")
