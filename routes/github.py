from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

# Load environment variables from root directory
current_file = Path(__file__).resolve()
root_dir = current_file.parent.parent  # Go up from routes/ to root/
env_path = root_dir / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path, verbose=True)
    print(f"✅ Environment loaded in github.py from: {env_path}")
else:
    print(f"❌ .env file not found at: {env_path}")

from db.database import get_database
from models.repository import Repository
from models.user import User
from services.github_fetcher import GitHubFetcher
from utils.token_storage import (
    store_github_token,
    is_github_connected,
    get_github_token,
)
from utils.dependencies import get_current_active_user, get_optional_current_user
from utils.auth import verify_token
import json

router = APIRouter()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
CALLBACK_URL = "http://localhost:8000/auth/github/callback"

# Rest of your existing code...


@router.get("/auth/github")
async def connect_github(
    token: Optional[str] = Query(None),
    db: Session = Depends(get_database)
):
    """Initiate GitHub OAuth for authenticated user"""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=500, 
            detail="GitHub OAuth not configured. Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET."
        )
    
    # Verify the token and get the user
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required")
    
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    # Store user state for callback
    state = user.id  # Use user ID as state
    github_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={CALLBACK_URL}&scope=user:email repo&state={state}"
    return RedirectResponse(url=github_url)


@router.get("/auth/github/callback")
async def github_callback(
    code: str, 
    state: str = None,
    db: Session = Depends(get_database)
):
    """Handle GitHub OAuth callback"""
    if not state:
        return RedirectResponse(url="/dashboard?error=invalid_state")
    
    # Find user by state (user ID)
    user = db.query(User).filter(User.id == state).first()
    if not user:
        return RedirectResponse(url="/dashboard?error=user_not_found")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )

        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return RedirectResponse(url="/dashboard?error=auth_failed")

        fetcher = GitHubFetcher(access_token)
        user_info = await fetcher.fetch_user_info()

        if not user_info:
            return RedirectResponse(url="/dashboard?error=user_fetch_failed")

        github_username = user_info["login"]
        
        # Update user's GitHub username
        user.github_username = github_username
        db.commit()

        # Store GitHub token for this user
        store_github_token(user.id, access_token)

        # Fetch repositories for this user
        filtered_repositories = await fetcher.fetch_and_filter_repositories(
            github_username, db, user.id
        )
        processed_count, skipped_count, deleted_count = (
            fetcher.save_filtered_repositories_to_db(
                filtered_repositories, github_username, db, user.id
            )
        )

        print(
            f"Initial sync: {processed_count} processed, {skipped_count} skipped, {deleted_count} deleted for user {user.username}"
        )

        return RedirectResponse(url="/dashboard?connected=true")


@router.get("/github/repos")
async def get_stored_repos(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Get stored repositories for authenticated user"""
    if not is_github_connected(current_user.id):
        raise HTTPException(status_code=400, detail="No GitHub connection found")

    # Only fetch eligible repositories for this user
    repositories = (
        db.query(Repository)
        .filter_by(user_id=current_user.id, is_eligible=True)
        .order_by(Repository.fetched_at.desc())
        .limit(20)
        .all()
    )

    total_count = (
        db.query(Repository)
        .filter_by(user_id=current_user.id, is_eligible=True)
        .count()
    )

    repo_list = []
    for repo in repositories:
        languages = json.loads(repo.languages_list) if repo.languages_list else []
        repo_list.append(
            {
                "name": repo.repo_name,
                "url": repo.repo_url,
                "description": repo.description or "No description",
                "language": repo.language or "Unknown",
                "languages": languages,
                "stars": repo.stars,
                "forks": repo.forks,
                "updated": (
                    repo.updated_at.isoformat() if repo.updated_at else "Unknown"
                ),
                "fetched_at": (
                    repo.fetched_at.isoformat() if repo.fetched_at else "Unknown"
                ),
                "has_readme": repo.has_readme,
                "readme_length": len(repo.readme_content) if repo.readme_content else 0,
            }
        )

    return {
        "repos": repo_list,
        "username": current_user.github_username,
        "total_count": total_count,
        "displayed_count": len(repo_list),
        "last_sync": repositories[0].fetched_at.isoformat() if repositories else None,
    }


@router.post("/github/refresh/{username}")
async def refresh_repositories(
    username: str, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    if not is_github_connected(current_user.id):
        raise HTTPException(status_code=400, detail="GitHub connection not found")

    access_token = get_github_token(current_user.id)
    if not access_token:
        raise HTTPException(status_code=400, detail="GitHub token not found")

    fetcher = GitHubFetcher(access_token)
    filtered_repositories = await fetcher.fetch_and_filter_repositories(username, db, current_user.id)
    processed_count, skipped_count, deleted_count = (
        fetcher.save_filtered_repositories_to_db(filtered_repositories, username, db, current_user.id)
    )

    return {
        "message": f"Incremental refresh completed for {username}",
        "processed": processed_count,
        "skipped": skipped_count,
        "deleted": deleted_count,
        "efficiency": f"{skipped_count}/{processed_count + skipped_count} repos skipped (no changes)",
        "cleanup": f"{deleted_count} repositories removed (no longer eligible)",
    }


@router.get("/github/connection-status")
async def get_connection_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    if not is_github_connected(current_user.id):
        return {"connected": False, "message": "No GitHub tokens stored"}

    repo_count = db.query(Repository).filter_by(user_id=current_user.id).count()

    latest_repo = (
        db.query(Repository)
        .filter_by(user_id=current_user.id)
        .order_by(Repository.fetched_at.desc())
        .first()
    )

    return {
        "connected": True,
        "username": current_user.github_username,
        "repository_count": repo_count,
        "last_fetch": latest_repo.fetched_at.isoformat() if latest_repo else None,
        "token_available": get_github_token(current_user.id) is not None,
    }
