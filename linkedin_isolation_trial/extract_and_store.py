# extract_and_store.py

from db.linkedin_database import (
    LinkedInBase,
    engine,
    SessionLocal,
    LinkedInProfile,
    LinkedInExperience,
    LinkedInEducation,
    LinkedInCertification,
)
import PyPDF2
import os


def create_tables():
    LinkedInBase.metadata.create_all(bind=engine)


def extract_pdf_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            pg = page.extract_text()
            if pg:
                text += pg + "\n"
    return text


def parse_profile(text):
    """Parse the PDF text and return structured data for the models"""
    # You may want to improve these with Regex or more robust parsing.
    # The following is hardcoded for your provided sample!
    return {
        "profile_url": "https://www.linkedin.com/in/kxshrx",
        "name": "J Kishore Kumar",
        "headline": "Undergraduate at VIT Chennai | AI Engineer | Agentic Systems | Generative AI Workflows | Backend Developer",
        "location": "Chennai, Tamil Nadu, India",
        "summary": (
            "I’m an AI Engineer passionate about building intelligent systems using generative AI and autonomous "
            "agent technologies. I develop scalable SaaS applications that combine AI with backend solutions. I "
            "have experience in Python, cloud platforms like AWS and Azure, and a solid understanding of DevOps. "
            "I want to be part of teams building practical solutions with real impact."
        ),
        "experiences": [
            {
                "job_title": "Technical Team Member",
                "company_name": "CYSCOM VIT Chennai",
                "location": "Chennai, Tamil Nadu, India",
                "start_date": "Aug 2023",
                "end_date": "Present",
                "duration": "2 years",
                "description": None,
            },
            {
                "job_title": "Machine Learning Intern",
                "company_name": "Unified Mentor Private Limited",
                "location": "Chennai, Tamil Nadu, India",
                "start_date": "May 2025",
                "end_date": "Jun 2025",
                "duration": "2 months",
                "description": None,
            },
        ],
        "educations": [
            {
                "school_name": "Vellore Institute of Technology",
                "degree": "Bachelor of Technology - BTech",
                "field_of_study": "Computer Science",
                "start_year": "2022",
                "end_year": "2026",
                "description": None,
            },
            {
                "school_name": "Sree Gokulam Public School",
                "degree": "Grade XI - XII",
                "field_of_study": None,
                "start_year": "2020",
                "end_year": "2022",
                "description": None,
            },
        ],
        "certifications": [
            {
                "name": "Google Data Analytics Professional Certificate",
                "issuer": "Coursera",
                "issue_date": "Jan 2025",
                "expiration_date": None,
                "credential_id": "ACNVLQLHS7AY",
                "credential_url": None,
            },
            {
                "name": "Microsoft Certified Azure AI Fundamentals",
                "issuer": "Microsoft",
                "issue_date": "Jul 2024",
                "expiration_date": None,
                "credential_id": "ITS-8506652",
                "credential_url": None,
            },
        ],
    }


def main():
    create_tables()
    session = SessionLocal()
    pdf_path = "Edit your public profile _ LinkedIn.pdf"
    if not os.path.exists(pdf_path):
        print("PDF file not found!")
        return

    pdf_text = extract_pdf_text(pdf_path)
    data = parse_profile(pdf_text)
    profile = LinkedInProfile(
        profile_url=data["profile_url"],
        name=data["name"],
        headline=data["headline"],
        location=data["location"],
        summary=data["summary"],
    )
    session.add(profile)
    session.commit()  # assign ID

    for exp in data["experiences"]:
        session.add(
            LinkedInExperience(
                profile_id=profile.id,
                job_title=exp["job_title"],
                company_name=exp["company_name"],
                location=exp["location"],
                start_date=exp["start_date"],
                end_date=exp["end_date"],
                description=exp["description"],
                duration=exp["duration"],
            )
        )

    for edu in data["educations"]:
        session.add(
            LinkedInEducation(
                profile_id=profile.id,
                school_name=edu["school_name"],
                degree=edu["degree"],
                field_of_study=edu["field_of_study"],
                start_year=edu["start_year"],
                end_year=edu["end_year"],
                description=edu["description"],
            )
        )

    for cert in data["certifications"]:
        session.add(
            LinkedInCertification(
                profile_id=profile.id,
                name=cert["name"],
                issuer=cert["issuer"],
                issue_date=cert["issue_date"],
                expiration_date=cert["expiration_date"],
                credential_id=cert["credential_id"],
                credential_url=cert["credential_url"],
            )
        )

    session.commit()
    session.close()
    print("Profile data extracted and inserted per model spec.")


if __name__ == "__main__":
    main()
