from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from routes.github import router as github_router
from db.database import create_tables

app = FastAPI(title="GitHub Repository Manager")

create_tables()

app.include_router(github_router)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    with open("dashboard.html", "r") as file:
        return HTMLResponse(content=file.read())

@app.get("/")
async def root():
    return {"message": "GitHub Repository Manager API"}
