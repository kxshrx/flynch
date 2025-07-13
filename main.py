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
from routes.linkedin import router as linkedin_router
from db.database import create_tables
from db.linkedin_database import create_linkedin_tables

app = FastAPI(title="GitHub Repository Manager")

# Create both databases
create_tables()
create_linkedin_tables()

# Include all routers
app.include_router(github_router)
app.include_router(analysis_router)
app.include_router(linkedin_router)

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

@app.get("/linkedin-scraper", response_class=HTMLResponse)
async def linkedin_scraper():
    with open("templates/linkedin_scraper.html", "r") as file:
        return HTMLResponse(content=file.read())
