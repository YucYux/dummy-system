"""
Configuration file for the Agent system.
Modify this file to change server settings, admin credentials, etc.
"""

import os

# Server Configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
DEBUG = True

# Security
SECRET_KEY = "change-this-to-a-random-secret-key-in-production"
JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60  # 24 hours in seconds

# Admin Configuration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Change this in production!

# Database Configuration
# Each user will have their own SQLite database file
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
USERS_DB_PATH = os.path.join(DATA_DIR, "users.db")  # Main users database
USER_DATA_DIR = os.path.join(DATA_DIR, "user_data")  # Individual user data

# Models Configuration Storage
MODELS_CONFIG_PATH = os.path.join(DATA_DIR, "models.json")

# CORS Configuration
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]  # Vue dev server

# LLM Default Settings
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7

# RAG Configuration
# Chunking settings (unit: tokens, calculated by tiktoken)
RAG_DEFAULT_CHUNK_SIZE = 512  # Default chunk size in tokens
RAG_MIN_CHUNK_SIZE = 100  # Minimum chunk size (won't split even if delimiter found)
RAG_CHUNK_OVERLAP = 50  # Overlap between chunks in tokens
RAG_CHUNK_DELIMITERS = ["\n\n", "\n", "。", ".", "！", "!", "？", "?"]  # Split on these (in priority order)

# RAG retrieval settings
RAG_TOP_K = 5  # Number of chunks to retrieve

# Embedding model configuration storage
EMBEDDING_CONFIG_PATH = os.path.join(DATA_DIR, "embedding_config.json")

# Document library storage
DOC_LIBRARY_DIR = os.path.join(DATA_DIR, "doc_libraries")  # Store document files and FAISS indexes
