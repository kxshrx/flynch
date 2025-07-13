from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# LinkedIn-specific database configuration
LinkedInBase = declarative_base()
linkedin_engine = create_engine("sqlite:///linkedin.db")
LinkedInSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=linkedin_engine)

def get_linkedin_database():
    """Dependency to get LinkedIn database session"""
    db = LinkedInSessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_linkedin_tables():
    """Create all LinkedIn-related tables"""
    from models.linkedin import LinkedInProfile, LinkedInExperience, LinkedInEducation, LinkedInCertification
    
    LinkedInBase.metadata.create_all(bind=linkedin_engine)
    print("LinkedIn database tables created successfully")
