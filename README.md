# Flynch - Professional Profile Manager

A simple web application for managing GitHub repositories, LinkedIn profiles, and AI-powered project analysis.

## Features

- **GitHub Integration**: Connect, view, and refresh GitHub repositories
- **LinkedIn Profile Upload**: Extract data from LinkedIn PDF exports
- **Project Analysis**: AI-powered repository analysis using Groq LLM
- **Clean HTML Interface**: Basic black/white theme for testing

## Quick Setup

### 1. Environment Variables

Create `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

### 2. Install & Run

```bash
pip install -r requirements.txt
python main.py
```

### 3. Access

- Open browser: `http://localhost:8000`
- Use the HTML interface to:
  - Connect GitHub (OAuth)
  - Upload LinkedIn PDFs
  - Analyze repositories with AI

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **AI**: Groq API with LangChain
- **Frontend**: Basic HTML/JavaScript
- **Services**: GitHub API, PDF extraction

## File Structure

```
├── main.py                   # FastAPI server
├── index.html               # Frontend interface
├── requirements.txt         # Dependencies
├── db/                      # Database setup
├── models/                  # Data models
├── routes/                  # API endpoints
├── services/                # Business logic
└── utils/                   # Helper functions
```

## API Endpoints

- `/auth/github` - GitHub OAuth
- `/github/repos` - Repository management
- `/linkedin/upload-pdf` - PDF processing
- `/github/analyze` - Project analysis
- `/analyzed-projects` - View results

## Notes

- Uses SQLite for data storage
- GitHub OAuth for repository access
- Groq API for AI analysis
- Basic prototyping interface
