"""
Centralized token storage for GitHub OAuth tokens
Now tied to authenticated users instead of global storage
"""

from typing import Dict, Optional


# Store GitHub tokens by user ID instead of username
user_github_tokens: Dict[str, str] = {}


def store_github_token(user_id: str, token: str):
    """Store GitHub token for a user"""
    user_github_tokens[user_id] = token
    print(f"✅ Token stored for user ID: {user_id}")


def get_github_token(user_id: str) -> Optional[str]:
    """Get GitHub token for a specific user"""
    return user_github_tokens.get(user_id)


def get_latest_username():
    """Get the most recently connected GitHub username - deprecated"""
    # This function is deprecated in favor of user-specific tokens
    return None


def is_github_connected(user_id: str = None) -> bool:
    """Check if GitHub connection exists for a user"""
    if user_id:
        return user_id in user_github_tokens
    return len(user_github_tokens) > 0


def clear_github_tokens():
    """Clear all stored tokens"""
    user_github_tokens.clear()


def clear_user_github_token(user_id: str):
    """Clear GitHub token for a specific user"""
    if user_id in user_github_tokens:
        del user_github_tokens[user_id]
        print(f"✅ Token cleared for user ID: {user_id}")
