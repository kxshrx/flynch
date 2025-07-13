import httpx
import json
import base64
from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models.repository import Repository
from utils.datetime_utils import DateTimeManager

class GitHubFetcher:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {"Authorization": f"token {access_token}"}
        self.dt_manager = DateTimeManager()
    
    async def fetch_user_info(self) -> Optional[Dict]:
        """Fetch GitHub user information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return None
    
    async def fetch_readme_content(self, username: str, repo_name: str) -> Optional[str]:
        """Fetch README content from a repository"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{username}/{repo_name}/readme",
                headers=self.headers
            )
            
            if response.status_code == 200:
                readme_data = response.json()
                content = readme_data.get("content", "")
                if content:
                    try:
                        return base64.b64decode(content).decode('utf-8')
                    except:
                        return None
            return None
    
    async def fetch_repository_languages(self, username: str, repo_name: str) -> List[str]:
        """Fetch programming languages used in a repository"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{username}/{repo_name}/languages",
                headers=self.headers
            )
            
            if response.status_code == 200:
                languages_data = response.json()
                return list(languages_data.keys())
            return []
    
    def meets_filtering_criteria(self, repo_data: Dict, readme_content: Optional[str]) -> bool:
        """
        Updated filtering criteria: Fetch all public repositories
        No filtering based on README or description content
        """
        return True

        
    async def fetch_and_filter_repositories(self, username: str, db: Session) -> List[Dict]:
        """Fetch repositories and only process those that need updates"""
        repositories = []
        page = 1
        per_page = 100
        
        # Get existing repositories from database for comparison
        existing_repos = {}
        db_repos = db.query(Repository).filter_by(owner_username=username).all()
        for repo in db_repos:
            existing_repos[repo.repo_id] = {
                'updated_at': repo.updated_at,
                'repo_object': repo
            }
        
        # Track which repositories are still active on GitHub
        active_repo_ids = set()
        
        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(
                    f"https://api.github.com/users/{username}/repos",
                    headers=self.headers,
                    params={
                        "per_page": per_page, 
                        "page": page, 
                        "type": "owner",
                        "visibility": "public"
                    }
                )
                
                if response.status_code != 200:
                    break
                
                repos = response.json()
                if not repos:
                    break
                
                for repo in repos:
                    repo_id = repo["id"]
                    repo_name = repo["name"]
                    github_updated_at = self.dt_manager.parse_github_datetime(repo["updated_at"])
                    
                    # Mark this repository as active
                    active_repo_ids.add(repo_id)
                    
                    print(f"🔍 Checking repository: {repo_name}")
                    
                    # Check if we need to process this repository
                    needs_processing = True
                    if repo_id in existing_repos:
                        db_updated_at = existing_repos[repo_id]['updated_at']
                        
                        # Use centralized datetime comparison
                        comparison = self.dt_manager.compare_datetimes(db_updated_at, github_updated_at)
                        if comparison >= 0:  # db_updated_at >= github_updated_at
                            print(f"⏭️  Skipping {repo_name}: No changes since last fetch")
                            needs_processing = False
                    
                    if needs_processing:
                        # Fetch additional data for ALL repositories (no filtering)
                        readme_content = await self.fetch_readme_content(username, repo_name)
                        languages = await self.fetch_repository_languages(username, repo_name)
                        
                        # Add enhanced data to repo - ALL repos are now eligible
                        repo['readme_content'] = readme_content
                        repo['languages_list'] = languages
                        repo['has_readme'] = readme_content is not None
                        repo['is_eligible'] = True
                        
                        repositories.append(repo)
                        print(f"✅ Queued for update: {repo_name}")
                
                page += 1
        
        # Check for repositories that no longer exist on GitHub
        for repo_id, repo_info in existing_repos.items():
            if repo_id not in active_repo_ids:
                print(f"🗑️  Repository no longer exists on GitHub: {repo_info['repo_object'].repo_name}")
                # Add to deletion list
                repositories.append({
                    'id': repo_id,
                    'name': repo_info['repo_object'].repo_name,
                    'should_delete': True,
                    'reason': 'deleted_from_github'
                })
        
        return repositories

    def save_filtered_repositories_to_db(self, repositories: List[Dict], username: str, db: Session):
        """Save changes and delete ineligible repositories from database"""
        current_time = self.dt_manager.now_utc()
        processed_count = 0
        skipped_count = 0
        deleted_count = 0
        
        for repo_data in repositories:
            repo_id = repo_data["id"]
            repo_name = repo_data["name"]
            
            # Check if repository should be deleted
            if repo_data.get('should_delete', False):
                existing_repo = db.query(Repository).filter_by(repo_id=repo_id).first()
                if existing_repo:
                    db.delete(existing_repo)
                    deleted_count += 1
                    reason = repo_data.get('reason', 'no longer meets criteria')
                    print(f"🗑️  Deleted {repo_name}: {reason}")
                continue
            
            # Parse GitHub datetime properly
            github_updated_at = self.dt_manager.parse_github_datetime(repo_data["updated_at"])
            github_created_at = self.dt_manager.parse_github_datetime(repo_data["created_at"])
            
            # Check if repository exists in database
            existing_repo = db.query(Repository).filter_by(repo_id=repo_id).first()
            
            if existing_repo:
                # Compare timestamps using centralized method
                comparison = self.dt_manager.compare_datetimes(existing_repo.updated_at, github_updated_at)
                if comparison >= 0:
                    print(f"⏭️  Skipped {repo_name}: No changes since {existing_repo.updated_at}")
                    skipped_count += 1
                    continue
                
                print(f"🔄 Updating {repo_name}: Changed from {existing_repo.updated_at} to {github_updated_at}")
                
                # Update existing repository
                existing_repo.repo_name = repo_data["name"]
                existing_repo.repo_url = repo_data["html_url"]
                existing_repo.description = repo_data.get("description", "")
                existing_repo.language = repo_data.get("language", "")
                existing_repo.topics = json.dumps(repo_data.get("topics", []))
                existing_repo.updated_at = github_updated_at
                existing_repo.stars = repo_data["stargazers_count"]
                existing_repo.forks = repo_data["forks_count"]
                existing_repo.fetched_at = current_time
                existing_repo.has_readme = repo_data.get("has_readme", False)
                existing_repo.readme_content = repo_data.get("readme_content")
                existing_repo.languages_list = json.dumps(repo_data.get("languages_list", []))
                existing_repo.is_eligible = repo_data.get("is_eligible", True)
                
            else:
                print(f"➕ Adding new repository: {repo_name}")
                
                # Create new repository record
                new_repo = Repository(
                    repo_id=repo_data["id"],
                    repo_name=repo_data["name"],
                    repo_url=repo_data["html_url"],
                    description=repo_data.get("description", ""),
                    language=repo_data.get("language", ""),
                    topics=json.dumps(repo_data.get("topics", [])),
                    created_at=github_created_at,
                    updated_at=github_updated_at,
                    stars=repo_data["stargazers_count"],
                    forks=repo_data["forks_count"],
                    fetched_at=current_time,
                    owner_username=username,
                    has_readme=repo_data.get("has_readme", False),
                    readme_content=repo_data.get("readme_content"),
                    languages_list=json.dumps(repo_data.get("languages_list", [])),
                    is_eligible=repo_data.get("is_eligible", True)
                )
                db.add(new_repo)
            
            processed_count += 1
        
        db.commit()
        print(f"✅ Database sync completed: {processed_count} updated, {skipped_count} skipped, {deleted_count} deleted")
        return processed_count, skipped_count, deleted_count
