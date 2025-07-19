#!/usr/bin/env python3
"""
Database migration script for Flynch application
This script helps migrate data and set up proper user relationships
"""

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def migrate_database():
    """Migrate the database to support user authentication"""
    
    print("🔄 Starting database migration...")
    
    # Connect to main database
    main_db_path = "github_repos.db"
    conn = sqlite3.connect(main_db_path)
    cursor = conn.cursor()
    
    try:
        # Check if users table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        
        if not cursor.fetchone():
            print("❌ Users table not found. Please run the application first to create tables.")
            return False
        
        # Check if there are any users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            print("ℹ️  No users found. You'll need to register first.")
        else:
            print(f"✅ Found {user_count} user(s) in the database")
        
        # Check LinkedIn database migration
        linkedin_db_path = "linkedin.db"
        if Path(linkedin_db_path).exists():
            print("🔄 Migrating LinkedIn data...")
            migrate_linkedin_data(linkedin_db_path, main_db_path)
        
        print("✅ Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        conn.close()


def migrate_linkedin_data(linkedin_db_path, main_db_path):
    """Migrate LinkedIn data from separate database to main database"""
    
    # Connect to both databases
    linkedin_conn = sqlite3.connect(linkedin_db_path)
    main_conn = sqlite3.connect(main_db_path)
    
    try:
        # Check if LinkedIn data exists
        linkedin_cursor = linkedin_conn.cursor()
        linkedin_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='linkedin_profiles'
        """)
        
        if not linkedin_cursor.fetchone():
            print("ℹ️  No LinkedIn data to migrate")
            return
        
        # Get LinkedIn profiles
        linkedin_cursor.execute("SELECT * FROM linkedin_profiles")
        profiles = linkedin_cursor.fetchall()
        
        if not profiles:
            print("ℹ️  No LinkedIn profiles to migrate")
            return
        
        # Get first user from main database (for demo purposes)
        main_cursor = main_conn.cursor()
        main_cursor.execute("SELECT id FROM users LIMIT 1")
        user_result = main_cursor.fetchone()
        
        if not user_result:
            print("❌ No users found to assign LinkedIn data to")
            return
        
        user_id = user_result[0]
        print(f"📝 Assigning LinkedIn data to user: {user_id}")
        
        # Note: In a real migration, you'd want to be more careful about user assignment
        # For now, we'll skip the migration and let users re-upload their LinkedIn data
        print("ℹ️  LinkedIn data migration skipped - please re-upload your LinkedIn PDF")
        
    except Exception as e:
        print(f"❌ LinkedIn migration failed: {e}")
    finally:
        linkedin_conn.close()
        main_conn.close()


def create_test_user():
    """Create a test user for development purposes"""
    
    print("🔄 Creating test user...")
    
    conn = sqlite3.connect("github_repos.db")
    cursor = conn.cursor()
    
    try:
        # Check if test user already exists
        cursor.execute("SELECT id FROM users WHERE username = 'testuser'")
        if cursor.fetchone():
            print("ℹ️  Test user already exists")
            return
        
        # Create test user
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Note: You'd need to hash the password properly in production
        # For demo, using a simple placeholder
        cursor.execute("""
            INSERT INTO users (id, username, email, hashed_password, full_name, is_active, is_verified, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            "testuser",
            "test@example.com",
            "$2b$12$placeholder_hash",  # This won't work for actual login
            "Test User",
            True,
            True,
            now,
            now
        ))
        
        conn.commit()
        print(f"✅ Test user created with ID: {user_id}")
        print("⚠️  Note: Test user has placeholder password - use register endpoint for real users")
        
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    print("🚀 Flynch Database Migration Script")
    print("=" * 50)
    
    success = migrate_database()
    
    if success:
        print("\n🎉 Migration completed! You can now:")
        print("1. Start the application: python main.py")
        print("2. Register a new user at: http://localhost:8000/")
        print("3. Login and use the application")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
