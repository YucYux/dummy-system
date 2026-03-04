"""
User model and database operations.
"""

import sqlite3
import os
import hashlib
import uuid
from datetime import datetime
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


def get_users_db():
    """Get connection to the main users database."""
    conn = sqlite3.connect(config.USERS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_users_db():
    """Initialize the users database with required tables."""
    conn = get_users_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            last_login TEXT
        )
    ''')
    
    conn.commit()
    
    # Create admin user if not exists
    cursor.execute('SELECT id FROM users WHERE username = ?', (config.ADMIN_USERNAME,))
    if not cursor.fetchone():
        create_user(config.ADMIN_USERNAME, config.ADMIN_PASSWORD, is_admin=True)
    
    conn.close()


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, password: str, is_admin: bool = False) -> dict:
    """Create a new user."""
    conn = get_users_db()
    cursor = conn.cursor()
    
    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)
    created_at = datetime.now().isoformat()
    
    try:
        cursor.execute('''
            INSERT INTO users (id, username, password_hash, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, password_hash, 1 if is_admin else 0, created_at))
        conn.commit()
        
        # Create user's personal database
        init_user_db(user_id)
        
        return {
            'id': user_id,
            'username': username,
            'is_admin': is_admin,
            'created_at': created_at
        }
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def verify_user(username: str, password: str) -> dict:
    """Verify user credentials and return user info."""
    conn = get_users_db()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute('''
        SELECT id, username, is_admin, created_at FROM users
        WHERE username = ? AND password_hash = ?
    ''', (username, password_hash))
    
    row = cursor.fetchone()
    
    if row:
        # Update last login time
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now().isoformat(), row['id']))
        conn.commit()
        
        user = {
            'id': row['id'],
            'username': row['username'],
            'is_admin': bool(row['is_admin']),
            'created_at': row['created_at']
        }
        conn.close()
        return user
    
    conn.close()
    return None


def get_user_by_id(user_id: str) -> dict:
    """Get user by ID."""
    conn = get_users_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, is_admin, created_at, last_login FROM users
        WHERE id = ?
    ''', (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row['id'],
            'username': row['username'],
            'is_admin': bool(row['is_admin']),
            'created_at': row['created_at'],
            'last_login': row['last_login']
        }
    return None


def get_all_users() -> list:
    """Get all users (for admin)."""
    conn = get_users_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, is_admin, created_at, last_login FROM users
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        'id': row['id'],
        'username': row['username'],
        'is_admin': bool(row['is_admin']),
        'created_at': row['created_at'],
        'last_login': row['last_login']
    } for row in rows]


def delete_user(user_id: str) -> bool:
    """Delete a user and their data."""
    conn = get_users_db()
    cursor = conn.cursor()
    
    # Check if user is admin
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False
    
    # Delete user from main database
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    # Delete user's personal database file
    user_db_path = get_user_db_path(user_id)
    if os.path.exists(user_db_path):
        os.remove(user_db_path)
    
    return True


def get_user_db_path(user_id: str) -> str:
    """Get the path to a user's personal database."""
    return os.path.join(config.USER_DATA_DIR, f"{user_id}.db")


def get_user_db(user_id: str):
    """Get connection to a user's personal database."""
    db_path = get_user_db_path(user_id)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_user_db(user_id: str):
    """Initialize a user's personal database."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    # Conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            model_id TEXT,
            reasoning_effort TEXT DEFAULT 'auto',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_calls TEXT,
            tool_call_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')
    
    conn.commit()
    conn.close()
