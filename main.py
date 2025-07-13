from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv, find_dotenv
import os

# Load environment variables
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file, verbose=True)

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

# ADD THIS BACKUP ROUTE
@app.get("/repo-selection", response_class=HTMLResponse)
async def repo_selection_backup():
    """Backup route for repository selection"""
    try:
        with open("templates/repo_selection.html", "r") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>Repository Selection</title></head>
            <body>
                <h1>Repository Selection</h1>
                <p>Template file not found. Please ensure templates/repo_selection.html exists.</p>
                <a href="/dashboard">Back to Dashboard</a>
            </body>
        </html>
        """)
