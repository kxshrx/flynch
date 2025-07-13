"""
Centralized token storage for GitHub OAuth tokens
Shared across all modules to maintain session state
"""

github_tokens = {}

def store_github_token(username: str, token: str):
    """Store GitHub token for a user"""
    github_tokens[username] = token
    print(f"✅ Token stored for user: {username}")

def get_github_token(username: str = None):
    """Get GitHub token for a user or the latest user"""
    if username:
        return github_tokens.get(username)
    
    if github_tokens:
        latest_username = list(github_tokens.keys())[-1]
        return github_tokens[latest_username]
    
    return None

def get_latest_username():
    """Get the most recently connected GitHub username"""
    if github_tokens:
        return list(github_tokens.keys())[-1]
    return None

def is_github_connected():
    """Check if any GitHub connection exists"""
    return len(github_tokens) > 0

def clear_github_tokens():
    """Clear all stored tokens"""
    github_tokens.clear()
