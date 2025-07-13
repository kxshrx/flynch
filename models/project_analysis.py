from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.types import TypeDecorator, DateTime as SQLDateTime
from db.database import Base
from datetime import datetime, timezone
import uuid

class UTCDateTime(TypeDecorator):
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
class ProjectAnalysis(Base):
    __tablename__ = "project_analysis"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_id = Column(Integer, nullable=False)
    repo_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    tech_stack = Column(Text, nullable=False)  # JSON string
    skills = Column(Text, nullable=False)      # JSON string
    domain = Column(String, nullable=False)
    impact = Column(Text, nullable=False)
    user_github_username = Column(String, nullable=False)
    analysis_status = Column(String, default="pending")  # pending, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(UTCDateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(UTCDateTime, default=lambda: datetime.now(timezone.utc))

    # New columns
    problem_solved = Column(Text, nullable=True)
    project_type = Column(String, nullable=True)
    responsibilities = Column(Text, nullable=True)
    key_features = Column(Text, nullable=True)
    used_llm_or_vector = Column(Boolean, default=False)
