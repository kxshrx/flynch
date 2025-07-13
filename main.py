from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables from root directory
current_file = Path(__file__).resolve()
root_dir = current_file.parent  # main.py is in root, so parent is root
env_path = root_dir / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=env_path, verbose=True)
    print(f"✅ Environment loaded in main.py from: {env_path}")
else:
    print(f"❌ .env file not found at: {env_path}")

from routes.github import router as github_router
from routes.analysis import router as analysis_router
from db.database import create_tables

app = FastAPI(title="GitHub Repository Manager")

create_tables()

app.include_router(github_router)
app.include_router(analysis_router)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    with open("dashboard.html", "r") as file:
        return HTMLResponse(content=file.read())

@app.get("/")
async def root():
    return {"message": "GitHub Repository Manager API"}

@app.get("/repo-selection", response_class=HTMLResponse)
async def repo_selection():
    with open("templates/repo_selection.html", "r") as file:
        return HTMLResponse(content=file.read())
