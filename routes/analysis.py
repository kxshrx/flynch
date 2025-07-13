from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import os
from db.database import get_database
from services.repo_analyzer import RepositoryAnalyzer
from models.project_analysis import ProjectAnalysis
from utils.token_storage import get_github_token, get_latest_username, is_github_connected
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from root directory
def load_environment_variables():
    """Load environment variables from root directory"""
    
    # Get the root directory (parent of routes directory)
    current_file = Path(__file__).resolve()
    root_dir = current_file.parent.parent  # Go up from routes/ to root/
    env_path = root_dir / '.env'
    
    if env_path.exists():
        loaded = load_dotenv(dotenv_path=env_path, verbose=True)
        if loaded:
            print(f"✅ Environment loaded from: {env_path}")
            return True
        else:
            print(f"❌ Failed to load from: {env_path}")
    else:
        print(f"❌ .env file not found at: {env_path}")
    
    # Fallback: try find_dotenv()
    from dotenv import find_dotenv
    env_file = find_dotenv()
    if env_file:
        loaded = load_dotenv(env_file, verbose=True)
        if loaded:
            print(f"✅ Environment loaded via find_dotenv from: {env_file}")
            return True
    
    return False

# Load environment variables
load_environment_variables()

# Verify critical variables
groq_key = os.getenv("GROQ_API_KEY")
if groq_key:
    print(f"✅ GROQ_API_KEY loaded (length: {len(groq_key)})")
else:
    print("❌ GROQ_API_KEY not found")
    print("Available environment variables:", [k for k in os.environ.keys() if 'GROQ' in k.upper() or 'GITHUB' in k.upper()])

router = APIRouter()

class AnalysisRequest(BaseModel):
    selected_repos: List[str]

@router.post("/github/analyze")
async def analyze_repositories(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database)
):
    print(f"Received analysis request: {request.selected_repos}")
    
    if not is_github_connected():
        raise HTTPException(status_code=400, detail="No GitHub connection found")
    
    if not request.selected_repos:
        raise HTTPException(status_code=400, detail="No repositories selected")
    
    # Get Groq API key with enhanced error handling
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ GROQ_API_KEY not found in environment variables")
        print("Available env vars:", [k for k in os.environ.keys() if 'GROQ' in k.upper()])
        raise HTTPException(status_code=500, detail="Groq API key not configured")
    
    print(f"✅ Using Groq API key (length: {len(groq_api_key)})")
    
    username = get_latest_username()
    access_token = get_github_token(username)
    
    if not access_token:
        raise HTTPException(status_code=400, detail="GitHub token not found")
    
    try:
        analyzer = RepositoryAnalyzer(groq_api_key)
        print("✅ RepositoryAnalyzer created successfully")
    except Exception as e:
        print(f"❌ Failed to create RepositoryAnalyzer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize analyzer: {e}")
    
    # Start analysis in background
    background_tasks.add_task(
        analyzer.analyze_repositories,
        request.selected_repos,
        username,
        db
    )
    
    return {
        "message": f"Analysis started for {len(request.selected_repos)} repositories",
        "repositories": request.selected_repos
    }

# Rest of your existing functions...
@router.get("/check-github-connection")
async def check_github_connection():
    if not is_github_connected():
        return {"connected": False, "message": "No GitHub connection found"}
    
    username = get_latest_username()
    return {"connected": True, "username": username}

@router.get("/analyzed-projects")
async def get_analyzed_projects(db: Session = Depends(get_database)):
    if not is_github_connected():
        raise HTTPException(status_code=400, detail="No GitHub connection found")
    
    username = get_latest_username()
    projects = db.query(ProjectAnalysis).filter_by(
        user_github_username=username
    ).order_by(ProjectAnalysis.created_at.desc()).all()
    
    project_list = []
    for project in projects:
        tech_stack = json.loads(project.tech_stack) if project.tech_stack else []
        skills = json.loads(project.skills) if project.skills else []
        
        project_list.append({
            "id": project.id,
            "repo_name": project.repo_name,
            "title": project.title,
            "summary": project.summary,
            "tech_stack": tech_stack,
            "skills": skills,
            "domain": project.domain,
            "impact": project.impact,
            "status": project.analysis_status,
            "error_message": project.error_message,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        })
    
    return {"projects": project_list, "total_count": len(project_list)}

@router.get("/repo-selection", response_class=HTMLResponse)
async def repo_selection_page():
    try:
        with open("templates/repo_selection.html", "r") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Template not found</h1><p>Please ensure templates/repo_selection.html exists.</p>")
