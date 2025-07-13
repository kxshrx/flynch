from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict
from db.linkedin_database import get_linkedin_database
from models.linkedin import LinkedInProfile, LinkedInExperience, LinkedInEducation, LinkedInCertification
from services.linkedin_scraper import LinkedInScraper

router = APIRouter()

class LinkedInScrapeRequest(BaseModel):
    profile_url: str

@router.post("/linkedin/scrape")
async def scrape_linkedin_profile(
    request: LinkedInScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_linkedin_database)
):
    """Scrape LinkedIn profile and store in database"""
    try:
        scraper = LinkedInScraper()
        
        if not scraper.validate_linkedin_url(request.profile_url):
            raise HTTPException(status_code=400, detail="Invalid LinkedIn profile URL")
        
        profile_data = await scraper.scrape_profile(request.profile_url)
        profile_id = scraper.save_to_database(profile_data, db)
        
        return {
            "message": "LinkedIn profile scraped successfully",
            "profile_id": profile_id,
            "profile_url": request.profile_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/linkedin/profiles")
async def get_linkedin_profiles(db: Session = Depends(get_linkedin_database)):
    """Get all LinkedIn profiles"""
    profiles = db.query(LinkedInProfile).all()
    
    profile_list = []
    for profile in profiles:
        profile_list.append({
            "id": profile.id,
            "profile_url": profile.profile_url,
            "name": profile.name,
            "headline": profile.headline,
            "location": profile.location,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        })
    
    return {"profiles": profile_list, "total_count": len(profile_list)}

@router.get("/linkedin/profile/{profile_id}")
async def get_linkedin_profile_details(
    profile_id: str,
    db: Session = Depends(get_linkedin_database)
):
    """Get detailed LinkedIn profile information"""
    profile = db.query(LinkedInProfile).filter_by(id=profile_id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    experiences = db.query(LinkedInExperience).filter_by(profile_id=profile_id).all()
    educations = db.query(LinkedInEducation).filter_by(profile_id=profile_id).all()
    certifications = db.query(LinkedInCertification).filter_by(profile_id=profile_id).all()
    
    return {
        "profile": {
            "id": profile.id,
            "profile_url": profile.profile_url,
            "name": profile.name,
            "headline": profile.headline,
            "location": profile.location,
            "summary": profile.summary,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        },
        "experience": [
            {
                "id": exp.id,
                "job_title": exp.job_title,
                "company_name": exp.company_name,
                "location": exp.location,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "description": exp.description,
                "duration": exp.duration
            }
            for exp in experiences
        ],
        "education": [
            {
                "id": edu.id,
                "school_name": edu.school_name,
                "degree": edu.degree,
                "field_of_study": edu.field_of_study,
                "start_year": edu.start_year,
                "end_year": edu.end_year,
                "description": edu.description
            }
            for edu in educations
        ],
        "certifications": [
            {
                "id": cert.id,
                "name": cert.name,
                "issuer": cert.issuer,
                "issue_date": cert.issue_date,
                "expiration_date": cert.expiration_date,
                "credential_id": cert.credential_id,
                "credential_url": cert.credential_url
            }
            for cert in certifications
        ]
    }

@router.get("/linkedin-scraper", response_class=HTMLResponse)
async def linkedin_scraper_page():
    """LinkedIn scraper interface"""
    try:
        with open("templates/linkedin_scraper.html", "r") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>LinkedIn Scraper Template Not Found</h1>")
