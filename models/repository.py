from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.types import TypeDecorator, DateTime as SQLDateTime
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime, timezone


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


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    repo_id = Column(Integer, unique=True, index=True)
    repo_name = Column(String, index=True)
    repo_url = Column(String)
    description = Column(Text)
    language = Column(String)
    topics = Column(Text)
    created_at = Column(UTCDateTime)
    updated_at = Column(UTCDateTime)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    fetched_at = Column(UTCDateTime, default=lambda: datetime.now(timezone.utc))
    owner_username = Column(String, index=True)
    has_readme = Column(Boolean, default=False)
    readme_content = Column(Text, nullable=True)
    languages_list = Column(Text, nullable=True)
    is_eligible = Column(Boolean, default=True)
    
    # Relationship to User
    user = relationship("User", back_populates="repositories")
