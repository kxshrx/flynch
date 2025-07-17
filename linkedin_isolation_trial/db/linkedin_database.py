# db/linkedin_database.py

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime, timezone
import uuid

LinkedInBase = declarative_base()


class LinkedInProfile(LinkedInBase):
    __tablename__ = "linkedin_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_url = Column(Text, unique=True, nullable=False, index=True)
    name = Column(Text, nullable=False)
    headline = Column(Text)
    location = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    experiences = relationship(
        "LinkedInExperience", back_populates="profile", cascade="all, delete-orphan"
    )
    educations = relationship(
        "LinkedInEducation", back_populates="profile", cascade="all, delete-orphan"
    )
    certifications = relationship(
        "LinkedInCertification", back_populates="profile", cascade="all, delete-orphan"
    )


class LinkedInExperience(LinkedInBase):
    __tablename__ = "linkedin_experience"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(
        String, ForeignKey("linkedin_profiles.id"), nullable=False, index=True
    )
    job_title = Column(Text, nullable=False)
    company_name = Column(Text, nullable=False)
    location = Column(Text)
    start_date = Column(Text)
    end_date = Column(Text)
    description = Column(Text)
    duration = Column(Text)

    profile = relationship("LinkedInProfile", back_populates="experiences")


class LinkedInEducation(LinkedInBase):
    __tablename__ = "linkedin_education"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(
        String, ForeignKey("linkedin_profiles.id"), nullable=False, index=True
    )
    school_name = Column(Text, nullable=False)
    degree = Column(Text)
    field_of_study = Column(Text)
    start_year = Column(Text)
    end_year = Column(Text)
    description = Column(Text)

    profile = relationship("LinkedInProfile", back_populates="educations")


class LinkedInCertification(LinkedInBase):
    __tablename__ = "linkedin_certifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(
        String, ForeignKey("linkedin_profiles.id"), nullable=False, index=True
    )
    name = Column(Text, nullable=False)
    issuer = Column(Text)
    issue_date = Column(Text)
    expiration_date = Column(Text)
    credential_id = Column(Text)
    credential_url = Column(Text)

    profile = relationship("LinkedInProfile", back_populates="certifications")


# Engine and sessionmaker for isolated DB
engine = create_engine("sqlite:///linkedin.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
