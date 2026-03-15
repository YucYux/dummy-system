"""
Document library model and database operations.
"""

import sqlite3
import os
import uuid
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from app.models.user import get_user_db


# Document library types
LIBRARY_TYPES = [
    "专业书籍",
    "设计规范",
    "产品手册",
    "专利文档",
    "百科数据"
]


def get_user_doc_dir(user_id: str) -> str:
    """Get the document directory path for a user."""
    return os.path.join(config.DOC_LIBRARY_DIR, user_id)


def get_library_dir(user_id: str, library_id: str) -> str:
    """Get the directory path for a specific library."""
    return os.path.join(get_user_doc_dir(user_id), library_id)


def ensure_user_doc_dir(user_id: str) -> str:
    """Ensure user's document directory exists."""
    path = get_user_doc_dir(user_id)
    os.makedirs(path, exist_ok=True)
    return path


def init_doc_library_tables(user_id: str):
    """Initialize document library tables in user's database."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    # Document libraries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doc_libraries (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            doc_count INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            chunk_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'ready',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # Documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            library_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            token_count INTEGER DEFAULT 0,
            chunk_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (library_id) REFERENCES doc_libraries (id)
        )
    ''')
    
    # Document chunks table (stores chunk metadata, vectors stored in FAISS)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doc_chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            library_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            token_count INTEGER DEFAULT 0,
            start_char INTEGER,
            end_char INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents (id),
            FOREIGN KEY (library_id) REFERENCES doc_libraries (id)
        )
    ''')
    
    # Conversation-Library binding table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_libraries (
            conversation_id TEXT NOT NULL,
            library_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (conversation_id, library_id),
            FOREIGN KEY (conversation_id) REFERENCES conversations (id),
            FOREIGN KEY (library_id) REFERENCES doc_libraries (id)
        )
    ''')
    
    # User embedding status table (tracks if user is currently embedding)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS embedding_status (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            is_embedding INTEGER DEFAULT 0,
            current_library_id TEXT,
            current_document_id TEXT,
            progress_percent REAL DEFAULT 0,
            started_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Initialize embedding status row
    cursor.execute('''
        INSERT OR IGNORE INTO embedding_status (id, is_embedding) VALUES (1, 0)
    ''')
    
    conn.commit()
    conn.close()


# ============ Library Operations ============

def create_library(user_id: str, name: str, library_type: str) -> Dict[str, Any]:
    """Create a new document library."""
    if library_type not in LIBRARY_TYPES:
        raise ValueError(f"Invalid library type. Must be one of: {LIBRARY_TYPES}")
    
    init_doc_library_tables(user_id)
    
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    library_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO doc_libraries (id, name, type, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (library_id, name, library_type, now, now))
    
    conn.commit()
    conn.close()
    
    # Create library directory
    library_dir = get_library_dir(user_id, library_id)
    os.makedirs(library_dir, exist_ok=True)
    os.makedirs(os.path.join(library_dir, "files"), exist_ok=True)
    
    return {
        'id': library_id,
        'name': name,
        'type': library_type,
        'doc_count': 0,
        'total_tokens': 0,
        'chunk_count': 0,
        'status': 'ready',
        'created_at': now,
        'updated_at': now
    }


def get_library(user_id: str, library_id: str) -> Optional[Dict[str, Any]]:
    """Get a library by ID."""
    init_doc_library_tables(user_id)
    
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM doc_libraries WHERE id = ?', (library_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_all_libraries(user_id: str) -> List[Dict[str, Any]]:
    """Get all libraries for a user."""
    init_doc_library_tables(user_id)
    
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM doc_libraries ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def update_library(user_id: str, library_id: str, name: str = None, library_type: str = None) -> Optional[Dict[str, Any]]:
    """Update library metadata."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    
    if library_type is not None:
        if library_type not in LIBRARY_TYPES:
            conn.close()
            raise ValueError(f"Invalid library type. Must be one of: {LIBRARY_TYPES}")
        updates.append("type = ?")
        params.append(library_type)
    
    if not updates:
        conn.close()
        return get_library(user_id, library_id)
    
    updates.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(library_id)
    
    cursor.execute(f'''
        UPDATE doc_libraries SET {", ".join(updates)} WHERE id = ?
    ''', params)
    
    conn.commit()
    conn.close()
    
    return get_library(user_id, library_id)


def delete_library(user_id: str, library_id: str) -> bool:
    """Delete a library and all its documents."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    # Check if library exists
    cursor.execute('SELECT id FROM doc_libraries WHERE id = ?', (library_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    # Delete chunks
    cursor.execute('DELETE FROM doc_chunks WHERE library_id = ?', (library_id,))
    
    # Delete documents
    cursor.execute('DELETE FROM documents WHERE library_id = ?', (library_id,))
    
    # Delete conversation bindings
    cursor.execute('DELETE FROM conversation_libraries WHERE library_id = ?', (library_id,))
    
    # Delete library
    cursor.execute('DELETE FROM doc_libraries WHERE id = ?', (library_id,))
    
    conn.commit()
    conn.close()
    
    # Delete library directory
    library_dir = get_library_dir(user_id, library_id)
    if os.path.exists(library_dir):
        shutil.rmtree(library_dir)
    
    return True


def update_library_stats(user_id: str, library_id: str):
    """Update library statistics (doc_count, total_tokens, chunk_count)."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    # Count documents
    cursor.execute('''
        SELECT COUNT(*) as count FROM documents 
        WHERE library_id = ? AND status = 'completed'
    ''', (library_id,))
    doc_count = cursor.fetchone()['count']
    
    # Sum tokens
    cursor.execute('''
        SELECT COALESCE(SUM(token_count), 0) as total FROM documents 
        WHERE library_id = ? AND status = 'completed'
    ''', (library_id,))
    total_tokens = cursor.fetchone()['total']
    
    # Count chunks
    cursor.execute('''
        SELECT COUNT(*) as count FROM doc_chunks WHERE library_id = ?
    ''', (library_id,))
    chunk_count = cursor.fetchone()['count']
    
    # Update library
    cursor.execute('''
        UPDATE doc_libraries 
        SET doc_count = ?, total_tokens = ?, chunk_count = ?, updated_at = ?
        WHERE id = ?
    ''', (doc_count, total_tokens, chunk_count, datetime.now().isoformat(), library_id))
    
    conn.commit()
    conn.close()


# ============ Document Operations ============

def add_document(user_id: str, library_id: str, filename: str, original_filename: str, file_size: int) -> Dict[str, Any]:
    """Add a document to a library."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    doc_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO documents (id, library_id, filename, original_filename, file_size, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
    ''', (doc_id, library_id, filename, original_filename, file_size, now, now))
    
    conn.commit()
    conn.close()
    
    return {
        'id': doc_id,
        'library_id': library_id,
        'filename': filename,
        'original_filename': original_filename,
        'file_size': file_size,
        'token_count': 0,
        'chunk_count': 0,
        'status': 'pending',
        'error_message': None,
        'created_at': now,
        'updated_at': now
    }


def get_document(user_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """Get a document by ID."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_library_documents(user_id: str, library_id: str) -> List[Dict[str, Any]]:
    """Get all documents in a library."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM documents WHERE library_id = ? ORDER BY created_at DESC
    ''', (library_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def update_document_status(user_id: str, doc_id: str, status: str, 
                           token_count: int = None, chunk_count: int = None,
                           error_message: str = None):
    """Update document processing status."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    updates = ["status = ?", "updated_at = ?"]
    params = [status, datetime.now().isoformat()]
    
    if token_count is not None:
        updates.append("token_count = ?")
        params.append(token_count)
    
    if chunk_count is not None:
        updates.append("chunk_count = ?")
        params.append(chunk_count)
    
    if error_message is not None:
        updates.append("error_message = ?")
        params.append(error_message)
    
    params.append(doc_id)
    
    cursor.execute(f'''
        UPDATE documents SET {", ".join(updates)} WHERE id = ?
    ''', params)
    
    conn.commit()
    conn.close()


def delete_document(user_id: str, doc_id: str) -> bool:
    """Delete a document and its chunks."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    # Get document info
    cursor.execute('SELECT library_id, filename FROM documents WHERE id = ?', (doc_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False
    
    library_id = row['library_id']
    filename = row['filename']
    
    # Delete chunks
    cursor.execute('DELETE FROM doc_chunks WHERE document_id = ?', (doc_id,))
    
    # Delete document
    cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
    
    conn.commit()
    conn.close()
    
    # Delete file
    file_path = os.path.join(get_library_dir(user_id, library_id), "files", filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Update library stats
    update_library_stats(user_id, library_id)
    
    return True


# ============ Chunk Operations ============

def add_chunks(user_id: str, doc_id: str, library_id: str, chunks: List[Dict[str, Any]]):
    """Add multiple chunks for a document."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    for chunk in chunks:
        chunk_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO doc_chunks (id, document_id, library_id, chunk_index, content, token_count, start_char, end_char, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (chunk_id, doc_id, library_id, chunk['index'], chunk['content'], 
              chunk['token_count'], chunk.get('start_char'), chunk.get('end_char'), now))
    
    conn.commit()
    conn.close()


def get_library_chunks(user_id: str, library_id: str) -> List[Dict[str, Any]]:
    """Get all chunks in a library."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.*, d.original_filename 
        FROM doc_chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.library_id = ?
        ORDER BY c.document_id, c.chunk_index
    ''', (library_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_chunks_by_ids(user_id: str, chunk_ids: List[str]) -> List[Dict[str, Any]]:
    """Get chunks by their IDs."""
    if not chunk_ids:
        return []
    
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    placeholders = ','.join(['?' for _ in chunk_ids])
    cursor.execute(f'''
        SELECT c.*, d.original_filename 
        FROM doc_chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.id IN ({placeholders})
    ''', chunk_ids)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


# ============ Conversation-Library Binding ============

def bind_library_to_conversation(user_id: str, conversation_id: str, library_id: str):
    """Bind a library to a conversation."""
    init_doc_library_tables(user_id)
    
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT OR IGNORE INTO conversation_libraries (conversation_id, library_id, created_at)
        VALUES (?, ?, ?)
    ''', (conversation_id, library_id, now))
    
    conn.commit()
    conn.close()


def unbind_library_from_conversation(user_id: str, conversation_id: str, library_id: str):
    """Unbind a library from a conversation."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM conversation_libraries WHERE conversation_id = ? AND library_id = ?
    ''', (conversation_id, library_id))
    
    conn.commit()
    conn.close()


def get_conversation_libraries(user_id: str, conversation_id: str) -> List[Dict[str, Any]]:
    """Get all libraries bound to a conversation."""
    init_doc_library_tables(user_id)
    
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT dl.* FROM doc_libraries dl
        JOIN conversation_libraries cl ON dl.id = cl.library_id
        WHERE cl.conversation_id = ?
    ''', (conversation_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def set_conversation_libraries(user_id: str, conversation_id: str, library_ids: List[str]):
    """Set the libraries bound to a conversation (replaces existing bindings)."""
    init_doc_library_tables(user_id)
    
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    # Remove existing bindings
    cursor.execute('DELETE FROM conversation_libraries WHERE conversation_id = ?', (conversation_id,))
    
    # Add new bindings
    now = datetime.now().isoformat()
    for library_id in library_ids:
        cursor.execute('''
            INSERT INTO conversation_libraries (conversation_id, library_id, created_at)
            VALUES (?, ?, ?)
        ''', (conversation_id, library_id, now))
    
    conn.commit()
    conn.close()


def validate_conversation_libraries(user_id: str, conversation_id: str) -> List[str]:
    """
    Validate conversation libraries and return list of deleted library IDs.
    Automatically unbinds deleted libraries.
    """
    init_doc_library_tables(user_id)
    
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    # Find libraries that no longer exist
    cursor.execute('''
        SELECT cl.library_id FROM conversation_libraries cl
        LEFT JOIN doc_libraries dl ON cl.library_id = dl.id
        WHERE cl.conversation_id = ? AND dl.id IS NULL
    ''', (conversation_id,))
    
    deleted_ids = [row['library_id'] for row in cursor.fetchall()]
    
    # Remove bindings to deleted libraries
    if deleted_ids:
        placeholders = ','.join(['?' for _ in deleted_ids])
        cursor.execute(f'''
            DELETE FROM conversation_libraries 
            WHERE conversation_id = ? AND library_id IN ({placeholders})
        ''', [conversation_id] + deleted_ids)
        conn.commit()
    
    conn.close()
    return deleted_ids


# ============ Embedding Status ============

def get_embedding_status(user_id: str) -> Dict[str, Any]:
    """Get current embedding status for a user."""
    init_doc_library_tables(user_id)
    
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM embedding_status WHERE id = 1')
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'is_embedding': bool(row['is_embedding']),
            'current_library_id': row['current_library_id'],
            'current_document_id': row['current_document_id'],
            'progress_percent': row['progress_percent'],
            'started_at': row['started_at'],
            'updated_at': row['updated_at']
        }
    return {'is_embedding': False}


def set_embedding_status(user_id: str, is_embedding: bool, library_id: str = None, 
                         document_id: str = None, progress: float = 0):
    """Set embedding status for a user."""
    init_doc_library_tables(user_id)
    
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    if is_embedding:
        cursor.execute('''
            UPDATE embedding_status SET 
                is_embedding = 1, 
                current_library_id = ?, 
                current_document_id = ?,
                progress_percent = ?,
                started_at = ?,
                updated_at = ?
            WHERE id = 1
        ''', (library_id, document_id, progress, now, now))
    else:
        cursor.execute('''
            UPDATE embedding_status SET 
                is_embedding = 0, 
                current_library_id = NULL, 
                current_document_id = NULL,
                progress_percent = 0,
                started_at = NULL,
                updated_at = ?
            WHERE id = 1
        ''', (now,))
    
    conn.commit()
    conn.close()


def update_embedding_progress(user_id: str, progress: float, document_id: str = None):
    """Update embedding progress."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    if document_id:
        cursor.execute('''
            UPDATE embedding_status SET 
                current_document_id = ?,
                progress_percent = ?,
                updated_at = ?
            WHERE id = 1
        ''', (document_id, progress, now))
    else:
        cursor.execute('''
            UPDATE embedding_status SET 
                progress_percent = ?,
                updated_at = ?
            WHERE id = 1
        ''', (progress, now))
    
    conn.commit()
    conn.close()
