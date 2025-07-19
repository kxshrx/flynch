#!/usr/bin/env python3
"""
Quick test script to verify authentication and GitHub OAuth setup
"""

import os
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

# API base URL
API_BASE = "http://localhost:8000"

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("🔐 Testing Authentication System...")
    
    # Test registration (this might fail if user exists, that's ok)
    print("\n1. Testing registration...")
    try:
        response = requests.post(f"{API_BASE}/auth/register", 
            json={
                "username": "testuser123",
                "email": "test123@example.com", 
                "password": "testpass123"
            }
        )
        if response.status_code == 200:
            print("✅ Registration successful")
        elif response.status_code == 400:
            print("ℹ️  User already exists (that's ok)")
        else:
            print(f"❌ Registration failed: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Registration error: {e}")
    
    # Test login
    print("\n2. Testing login...")
    try:
        response = requests.post(f"{API_BASE}/auth/login",
            json={
                "username": "testuser123",
                "password": "testpass123"
            }
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print("✅ Login successful")
            print(f"Token: {token[:20]}...")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_github_oauth(token):
    """Test GitHub OAuth endpoint"""
    print("\n🐙 Testing GitHub OAuth...")
    
    if not token:
        print("❌ No token available, skipping GitHub test")
        return
    
    try:
        response = requests.get(f"{API_BASE}/auth/github",
            headers={"Authorization": f"Bearer {token}"},
            allow_redirects=False
        )
        if response.status_code == 302:
            print("✅ GitHub OAuth redirect working")
            print(f"Redirect URL: {response.headers.get('location', 'Not found')[:100]}...")
        else:
            print(f"❌ GitHub OAuth failed: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ GitHub OAuth error: {e}")

def test_environment_variables():
    """Test environment variables"""
    print("\n🔧 Testing Environment Variables...")
    
    github_client_id = os.getenv("GITHUB_CLIENT_ID")
    github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    secret_key = os.getenv("SECRET_KEY")
    
    if github_client_id:
        print(f"✅ GITHUB_CLIENT_ID: {github_client_id[:10]}...")
    else:
        print("❌ GITHUB_CLIENT_ID not set")
    
    if github_client_secret:
        print(f"✅ GITHUB_CLIENT_SECRET: {github_client_secret[:10]}...")
    else:
        print("❌ GITHUB_CLIENT_SECRET not set")
    
    if secret_key:
        print(f"✅ SECRET_KEY: {secret_key[:10]}...")
    else:
        print("❌ SECRET_KEY not set")

if __name__ == "__main__":
    print("🧪 Flynch Authentication Test Suite")
    print("=" * 50)
    
    test_environment_variables()
    token = test_auth_endpoints()
    test_github_oauth(token)
    
    print("\n" + "=" * 50)
    print("Test completed! Check results above.")
