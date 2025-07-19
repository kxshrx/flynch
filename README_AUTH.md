# Flynch - Professional Profile Manager

A comprehensive web application for managing GitHub repositories, LinkedIn profiles, and project analysis with complete user authentication and authorization.

## 🚀 Features

- **Complete User Authentication & Authorization**

  - User registration and login with JWT tokens
  - Secure password hashing with bcrypt
  - Protected routes requiring authentication
  - User-specific data isolation

- **GitHub Integration**

  - OAuth-based GitHub connection
  - Repository fetching and management
  - User-specific repository access

- **LinkedIn Profile Management**

  - PDF upload and parsing
  - Profile data extraction and storage
  - User-specific profile management

- **AI-Powered Project Analysis**
  - Repository analysis using LangChain
  - AI-generated project summaries
  - Technology stack detection
  - Skills and impact analysis

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8+
- GitHub account for OAuth setup
- Groq API key for AI analysis

### 1. Clone and Install

```bash
git clone <repository-url>
cd flynch
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
# GitHub OAuth (required for GitHub integration)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Groq API (required for AI analysis)
GROQ_API_KEY=your_groq_api_key

# JWT Secret (required for authentication)
SECRET_KEY=your-super-secure-secret-key-change-this-in-production

# Optional: Database URL (defaults to SQLite)
DATABASE_URL=sqlite:///github_repos.db
```

#### Setting up GitHub OAuth:

1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Create a new OAuth App with:
   - Application name: "Flynch"
   - Homepage URL: `http://localhost:8000`
   - Authorization callback URL: `http://localhost:8000/auth/github/callback`
3. Copy the Client ID and Client Secret to your `.env` file

#### Getting Groq API Key:

1. Visit [Groq Console](https://console.groq.com/)
2. Sign up/login and create an API key
3. Add it to your `.env` file

### 3. Database Setup

Initialize the database:

```bash
python migrate_db.py
```

### 4. Run the Application

```bash
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`

## 📱 Usage

### First Time Setup

1. **Register**: Go to `http://localhost:8000` and create a new account
2. **Login**: Use your credentials to access the dashboard
3. **Connect GitHub**: Go to the GitHub section and connect your account
4. **Upload LinkedIn**: Upload your LinkedIn PDF in the LinkedIn section
5. **Analyze Projects**: Select repositories for AI-powered analysis

### User Authentication Flow

- **Landing Page**: Redirects to login if not authenticated
- **Registration**: Create new account with username, email, and password
- **Login**: Authenticate with username/email and password
- **Protected Access**: All application features require authentication
- **Data Isolation**: Users only see their own data

## 🔐 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt for secure password storage
- **User Data Isolation**: Each user only accesses their own data
- **Protected Routes**: All API endpoints require authentication
- **Secure Token Storage**: Client-side JWT token management
- **Session Management**: Automatic token validation and renewal

## 🚨 Important Security Notes

1. **Change SECRET_KEY**: Use a strong, unique secret key in production
2. **HTTPS in Production**: Always use HTTPS for authentication
3. **Token Expiration**: Tokens expire in 30 minutes by default
4. **Environment Variables**: Never commit `.env` file to version control

## 📝 API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints

- **Authentication**

  - `POST /auth/register` - Register new user
  - `POST /auth/login` - User login
  - `GET /auth/me` - Get current user info

- **GitHub** (Protected)

  - `GET /auth/github` - Initiate GitHub OAuth
  - `GET /github/repos` - Get user repositories
  - `POST /github/refresh/{username}` - Refresh repositories

- **LinkedIn** (Protected)

  - `POST /linkedin/upload-pdf` - Upload LinkedIn PDF
  - `GET /linkedin/profiles` - Get user profiles
  - `GET /linkedin/profile/{id}` - Get profile details

- **Analysis** (Protected)
  - `POST /github/analyze` - Analyze repositories
  - `GET /analyzed-projects` - Get analysis results

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**: Check SECRET_KEY and token expiration
2. **GitHub OAuth**: Verify client ID/secret and callback URL
3. **Database Issues**: Run migration script and check permissions
4. **Groq API**: Verify API key and rate limits

---

**Note**: This application includes complete user authentication and authorization. All data is user-specific and protected. Make sure to properly configure environment variables before running.
