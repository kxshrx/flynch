from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from root directory
current_file = Path(__file__).resolve()
root_dir = current_file.parent.parent  # Go up from routes/ to root/
env_path = root_dir / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=env_path, verbose=True)
    print(f"✅ Environment loaded in github.py from: {env_path}")
else:
    print(f"❌ .env file not found at: {env_path}")

from db.database import get_database
from models.repository import Repository
from services.github_fetcher import GitHubFetcher
from utils.token_storage import store_github_token, is_github_connected, get_latest_username, get_github_token
import json

router = APIRouter()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
CALLBACK_URL = "http://localhost:8000/auth/github/callback"

# Rest of your existing code...

@router.get("/auth/github")
async def connect_github():
    github_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={CALLBACK_URL}&scope=user:email repo"
    return RedirectResponse(url=github_url)

@router.get("/auth/github/callback")
async def github_callback(code: str, db: Session = Depends(get_database)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"}
        )
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            return RedirectResponse(url="/dashboard?error=auth_failed")
        
        fetcher = GitHubFetcher(access_token)
        user_info = await fetcher.fetch_user_info()
        
        if not user_info:
            return RedirectResponse(url="/dashboard?error=user_fetch_failed")
        
        username = user_info["login"]
        
        # Use centralized token storage
        store_github_token(username, access_token)
        
        filtered_repositories = await fetcher.fetch_and_filter_repositories(username, db)
        processed_count, skipped_count, deleted_count = fetcher.save_filtered_repositories_to_db(filtered_repositories, username, db)
        
        print(f"Initial sync: {processed_count} processed, {skipped_count} skipped, {deleted_count} deleted for {username}")
        
        return RedirectResponse(url="/dashboard?connected=true")

@router.get("/github/repos")
async def get_stored_repos(db: Session = Depends(get_database)):
    if not is_github_connected():
        raise HTTPException(status_code=400, detail="No GitHub connection found")
    
    latest_username = get_latest_username()
    
    # Only fetch eligible repositories
    repositories = db.query(Repository).filter_by(
        owner_username=latest_username,
        is_eligible=True
    ).order_by(Repository.fetched_at.desc()).limit(20).all()
    
    total_count = db.query(Repository).filter_by(
        owner_username=latest_username,
        is_eligible=True
    ).count()
    
    repo_list = []
    for repo in repositories:
        languages = json.loads(repo.languages_list) if repo.languages_list else []
        repo_list.append({
            "name": repo.repo_name,
            "url": repo.repo_url,
            "description": repo.description or "No description",
            "language": repo.language or "Unknown",
            "languages": languages,
            "stars": repo.stars,
            "forks": repo.forks,
            "updated": repo.updated_at.isoformat() if repo.updated_at else "Unknown",
            "fetched_at": repo.fetched_at.isoformat() if repo.fetched_at else "Unknown",
            "has_readme": repo.has_readme,
            "readme_length": len(repo.readme_content) if repo.readme_content else 0
        })
    
    return {
        "repos": repo_list,
        "username": latest_username,
        "total_count": total_count,
        "displayed_count": len(repo_list),
        "last_sync": repositories[0].fetched_at.isoformat() if repositories else None
    }

@router.post("/github/refresh/{username}")
async def refresh_repositories(username: str, db: Session = Depends(get_database)):
    if not is_github_connected():
        raise HTTPException(status_code=400, detail="GitHub connection not found")
    
    access_token = get_github_token(username)
    if not access_token:
        raise HTTPException(status_code=400, detail="GitHub token not found")
    
    fetcher = GitHubFetcher(access_token)
    filtered_repositories = await fetcher.fetch_and_filter_repositories(username, db)
    processed_count, skipped_count, deleted_count = fetcher.save_filtered_repositories_to_db(filtered_repositories, username, db)
    
    return {
        "message": f"Incremental refresh completed for {username}",
        "processed": processed_count,
        "skipped": skipped_count,
        "deleted": deleted_count,
        "efficiency": f"{skipped_count}/{processed_count + skipped_count} repos skipped (no changes)",
        "cleanup": f"{deleted_count} repositories removed (no longer eligible)"
    }

@router.get("/github/connection-status")
async def get_connection_status(db: Session = Depends(get_database)):
    if not is_github_connected():
        return {"connected": False, "message": "No GitHub tokens stored"}
    
    latest_username = get_latest_username()
    repo_count = db.query(Repository).filter_by(owner_username=latest_username).count()
    
    latest_repo = db.query(Repository).filter_by(
        owner_username=latest_username
    ).order_by(Repository.fetched_at.desc()).first()
    
    return {
        "connected": True,
        "username": latest_username,
        "repository_count": repo_count,
        "last_fetch": latest_repo.fetched_at.isoformat() if latest_repo else None,
        "token_available": get_github_token(latest_username) is not None
    }
