from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create both databases
create_tables()
create_linkedin_tables()

# Include all routers
app.include_router(github_router)
app.include_router(analysis_router)
app.include_router(linkedin_router)


@app.get("/")
async def root():
    return FileResponse("index.html")


@app.get("/dashboard")
async def dashboard():
    return FileResponse("index.html")
