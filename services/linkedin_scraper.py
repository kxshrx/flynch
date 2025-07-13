import re
from typing import Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from langchain_community.document_loaders import WebBaseLoader
from bs4 import BeautifulSoup
import requests

from models.linkedin import LinkedInProfile, LinkedInExperience, LinkedInEducation, LinkedInCertification

class LinkedInScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def validate_linkedin_url(self, url: str) -> bool:
        """Validate if the URL is a valid LinkedIn profile URL"""
        linkedin_pattern = r'^https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-]+/?$'
        return bool(re.match(linkedin_pattern, url))
    
    async def scrape_profile(self, profile_url: str) -> Dict:
        """Scrape LinkedIn profile using LangChain WebBaseLoader"""
        if not self.validate_linkedin_url(profile_url):
            raise ValueError("Invalid LinkedIn profile URL")
        
        try:
            loader = WebBaseLoader(profile_url)
            docs = loader.load()
            
            if not docs:
                raise Exception("Failed to load profile content")
            
            html_content = docs[0].page_content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            profile_data = self.parse_profile_data(soup, profile_url)
            return profile_data
            
        except Exception as e:
            return await self.scrape_with_requests(profile_url)
    
    async def scrape_with_requests(self, profile_url: str) -> Dict:
        """Fallback scraping method using requests"""
        try:
            response = requests.get(profile_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self.parse_profile_data(soup, profile_url)
            
        except Exception as e:
            raise Exception(f"Failed to scrape LinkedIn profile: {str(e)}")
    
    def parse_profile_data(self, soup: BeautifulSoup, profile_url: str) -> Dict:
        """Parse LinkedIn profile data from BeautifulSoup object"""
        profile_data = {
            "profile_url": profile_url,
            "name": self.extract_name(soup),
            "headline": self.extract_headline(soup),
            "location": self.extract_location(soup),
            "summary": self.extract_summary(soup),
            "experience": self.extract_experience(soup),
            "education": self.extract_education(soup),
            "certifications": self.extract_certifications(soup)
        }
        
        return profile_data
    
    def extract_name(self, soup: BeautifulSoup) -> str:
        """Extract full name from profile"""
        selectors = [
            'h1.text-heading-xlarge',
            'h1.top-card-layout__title',
            '.pv-text-details__left-panel h1',
            '.ph5 h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def extract_headline(self, soup: BeautifulSoup) -> str:
        """Extract professional headline"""
        selectors = [
            '.text-body-medium.break-words',
            '.top-card-layout__headline',
            '.pv-text-details__left-panel .text-body-medium'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def extract_location(self, soup: BeautifulSoup) -> str:
        """Extract location information"""
        selectors = [
            '.text-body-small.inline.t-black--light.break-words',
            '.top-card-layout__first-subline',
            '.pv-text-details__left-panel .text-body-small'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if any(word in text.lower() for word in ['area', 'city', 'state', 'country']):
                    return text
        
        return ""
    
    def extract_summary(self, soup: BeautifulSoup) -> str:
        """Extract about/summary section"""
        selectors = [
            '#about ~ .pv-shared-text-with-see-more',
            '.pv-about__summary-text',
            '.core-section-container__content .pv-shared-text-with-see-more'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def extract_experience(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract work experience"""
        experiences = []
        
        experience_sections = soup.find_all('section', {'id': 'experience'}) or \
                            soup.find_all('div', {'data-section': 'experience'}) or \
                            soup.select('.experience-section')
        
        for section in experience_sections:
            exp_items = section.find_all('li') or section.find_all('.pv-entity__summary-info')
            
            for item in exp_items:
                experience = self.parse_experience_item(item)
                if experience:
                    experiences.append(experience)
        
        return experiences
    
    def parse_experience_item(self, item) -> Optional[Dict]:
        """Parse individual experience item"""
        try:
            job_title = ""
            company_name = ""
            location = ""
            start_date = ""
            end_date = ""
            description = ""
            duration = ""
            
            title_selectors = ['.pv-entity__summary-info h3', '.t-16.t-black.t-bold', 'h3']
            for selector in title_selectors:
                title_elem = item.select_one(selector)
                if title_elem:
                    job_title = title_elem.get_text(strip=True)
                    break
            
            company_selectors = ['.pv-entity__secondary-title', '.t-14.t-black', '.t-14.t-black--light']
            for selector in company_selectors:
                company_elem = item.select_one(selector)
                if company_elem:
                    company_name = company_elem.get_text(strip=True)
                    break
            
            date_selectors = ['.pv-entity__date-range', '.t-14.t-black--light.t-normal']
            for selector in date_selectors:
                date_elem = item.select_one(selector)
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    start_date, end_date, duration = self.parse_date_range(date_text)
                    break
            
            desc_selectors = ['.pv-entity__description', '.pv-shared-text-with-see-more']
            for selector in desc_selectors:
                desc_elem = item.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    break
            
            if job_title and company_name:
                return {
                    "job_title": job_title,
                    "company_name": company_name,
                    "location": location,
                    "start_date": start_date,
                    "end_date": end_date,
                    "description": description,
                    "duration": duration
                }
        
        except Exception as e:
            print(f"Error parsing experience item: {e}")
        
        return None
    
    def extract_education(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract education information"""
        educations = []
        
        education_sections = soup.find_all('section', {'id': 'education'}) or \
                           soup.find_all('div', {'data-section': 'education'}) or \
                           soup.select('.education-section')
        
        for section in education_sections:
            edu_items = section.find_all('li') or section.find_all('.pv-entity__summary-info')
            
            for item in edu_items:
                education = self.parse_education_item(item)
                if education:
                    educations.append(education)
        
        return educations
    
    def parse_education_item(self, item) -> Optional[Dict]:
        """Parse individual education item"""
        try:
            school_name = ""
            degree = ""
            field_of_study = ""
            start_year = ""
            end_year = ""
            description = ""
            
            school_selectors = ['.pv-entity__school-name', 'h3', '.t-16.t-black.t-bold']
            for selector in school_selectors:
                school_elem = item.select_one(selector)
                if school_elem:
                    school_name = school_elem.get_text(strip=True)
                    break
            
            degree_selectors = ['.pv-entity__degree-name', '.pv-entity__secondary-title']
            for selector in degree_selectors:
                degree_elem = item.select_one(selector)
                if degree_elem:
                    degree_text = degree_elem.get_text(strip=True)
                    if ',' in degree_text:
                        degree, field_of_study = degree_text.split(',', 1)
                        degree = degree.strip()
                        field_of_study = field_of_study.strip()
                    else:
                        degree = degree_text
                    break
            
            date_selectors = ['.pv-entity__dates', '.t-14.t-black--light']
            for selector in date_selectors:
                date_elem = item.select_one(selector)
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    start_year, end_year = self.parse_education_years(date_text)
                    break
            
            if school_name:
                return {
                    "school_name": school_name,
                    "degree": degree,
                    "field_of_study": field_of_study,
                    "start_year": start_year,
                    "end_year": end_year,
                    "description": description
                }
        
        except Exception as e:
            print(f"Error parsing education item: {e}")
        
        return None
    
    def extract_certifications(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract certifications"""
        certifications = []
        
        cert_sections = soup.find_all('section', {'id': 'certifications'}) or \
                       soup.find_all('div', {'data-section': 'certifications'}) or \
                       soup.select('.certifications-section')
        
        for section in cert_sections:
            cert_items = section.find_all('li') or section.find_all('.pv-entity__summary-info')
            
            for item in cert_items:
                certification = self.parse_certification_item(item)
                if certification:
                    certifications.append(certification)
        
        return certifications
    
    def parse_certification_item(self, item) -> Optional[Dict]:
        """Parse individual certification item"""
        try:
            name = ""
            issuer = ""
            issue_date = ""
            expiration_date = ""
            credential_id = ""
            credential_url = ""
            
            name_selectors = ['.pv-entity__summary-info h3', 'h3', '.t-16.t-black.t-bold']
            for selector in name_selectors:
                name_elem = item.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    break
            
            issuer_selectors = ['.pv-entity__secondary-title', '.t-14.t-black']
            for selector in issuer_selectors:
                issuer_elem = item.select_one(selector)
                if issuer_elem:
                    issuer = issuer_elem.get_text(strip=True)
                    break
            
            date_selectors = ['.pv-entity__date-range', '.t-14.t-black--light']
            for selector in date_selectors:
                date_elem = item.select_one(selector)
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    issue_date, expiration_date = self.parse_certification_dates(date_text)
                    break
            
            if name:
                return {
                    "name": name,
                    "issuer": issuer,
                    "issue_date": issue_date,
                    "expiration_date": expiration_date,
                    "credential_id": credential_id,
                    "credential_url": credential_url
                }
        
        except Exception as e:
            print(f"Error parsing certification item: {e}")
        
        return None
    
    def parse_date_range(self, date_text: str) -> tuple:
        """Parse date range text into start_date, end_date, duration"""
        start_date = ""
        end_date = ""
        duration = ""
        
        if "Present" in date_text or "present" in date_text:
            end_date = "Present"
        
        duration_match = re.search(r'\(([^)]+)\)', date_text)
        if duration_match:
            duration = duration_match.group(1)
        
        date_parts = date_text.replace(f"({duration})", "").strip().split(" – ")
        if len(date_parts) >= 2:
            start_date = date_parts[0].strip()
            end_date = date_parts[1].strip()
        elif len(date_parts) == 1:
            start_date = date_parts[0].strip()
        
        return start_date, end_date, duration
    
    def parse_education_years(self, date_text: str) -> tuple:
        """Parse education years"""
        years = re.findall(r'\b(19|20)\d{2}\b', date_text)
        start_year = years[0] if len(years) > 0 else ""
        end_year = years[1] if len(years) > 1 else ""
        return start_year, end_year
    
    def parse_certification_dates(self, date_text: str) -> tuple:
        """Parse certification dates"""
        issue_date = ""
        expiration_date = ""
        
        if "Expires" in date_text:
            parts = date_text.split("Expires")
            issue_date = parts[0].replace("Issued", "").strip()
            expiration_date = parts[1].strip()
        else:
            issue_date = date_text.replace("Issued", "").strip()
        
        return issue_date, expiration_date
    
    def save_to_database(self, profile_data: Dict, db: Session) -> str:
        """Save scraped profile data to database"""
        try:
            existing_profile = db.query(LinkedInProfile).filter_by(
                profile_url=profile_data["profile_url"]
            ).first()
            
            if existing_profile:
                profile = existing_profile
                profile.name = profile_data["name"]
                profile.headline = profile_data["headline"]
                profile.location = profile_data["location"]
                profile.summary = profile_data["summary"]
                profile.updated_at = datetime.now(timezone.utc)
                
                db.query(LinkedInExperience).filter_by(profile_id=profile.id).delete()
                db.query(LinkedInEducation).filter_by(profile_id=profile.id).delete()
                db.query(LinkedInCertification).filter_by(profile_id=profile.id).delete()
            else:
                profile = LinkedInProfile(
                    profile_url=profile_data["profile_url"],
                    name=profile_data["name"],
                    headline=profile_data["headline"],
                    location=profile_data["location"],
                    summary=profile_data["summary"]
                )
                db.add(profile)
                db.flush()
            
            for exp_data in profile_data["experience"]:
                experience = LinkedInExperience(
                    profile_id=profile.id,
                    job_title=exp_data["job_title"],
                    company_name=exp_data["company_name"],
                    location=exp_data.get("location", ""),
                    start_date=exp_data.get("start_date", ""),
                    end_date=exp_data.get("end_date", ""),
                    description=exp_data.get("description", ""),
                    duration=exp_data.get("duration", "")
                )
                db.add(experience)
            
            for edu_data in profile_data["education"]:
                education = LinkedInEducation(
                    profile_id=profile.id,
                    school_name=edu_data["school_name"],
                    degree=edu_data.get("degree", ""),
                    field_of_study=edu_data.get("field_of_study", ""),
                    start_year=edu_data.get("start_year", ""),
                    end_year=edu_data.get("end_year", ""),
                    description=edu_data.get("description", "")
                )
                db.add(education)
            
            for cert_data in profile_data["certifications"]:
                certification = LinkedInCertification(
                    profile_id=profile.id,
                    name=cert_data["name"],
                    issuer=cert_data.get("issuer", ""),
                    issue_date=cert_data.get("issue_date", ""),
                    expiration_date=cert_data.get("expiration_date", ""),
                    credential_id=cert_data.get("credential_id", ""),
                    credential_url=cert_data.get("credential_url", "")
                )
                db.add(certification)
            
            db.commit()
            return profile.id
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to save profile to database: {str(e)}")
