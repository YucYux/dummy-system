"""
Conversation and message operations for user's personal database.
"""

import uuid
import json
from datetime import datetime
from app.models.user import get_user_db


def create_conversation(user_id: str, title: str = "New Chat", 
                        model_id: str = None, reasoning_effort: str = 'auto') -> dict:
    """Create a new conversation for a user."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    conversation_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO conversations (id, title, model_id, reasoning_effort, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (conversation_id, title, model_id, reasoning_effort, now, now))
    
    conn.commit()
    conn.close()
    
    return {
        'id': conversation_id,
        'title': title,
        'model_id': model_id,
        'created_at': now,
        'updated_at': now
    }


def get_conversations(user_id: str) -> list:
    """Get all conversations for a user."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, model_id, reasoning_effort, created_at, updated_at 
        FROM conversations 
        ORDER BY updated_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        'id': row['id'],
        'title': row['title'],
        'model_id': row['model_id'],
        'reasoning_effort': row['reasoning_effort'] or 'auto',
        'created_at': row['created_at'],
        'updated_at': row['updated_at']
    } for row in rows]


def get_conversation(user_id: str, conversation_id: str) -> dict:
    """Get a specific conversation."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, model_id, reasoning_effort, created_at, updated_at 
        FROM conversations 
        WHERE id = ?
    ''', (conversation_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row['id'],
            'title': row['title'],
            'model_id': row['model_id'],
        'reasoning_effort': row['reasoning_effort'] or 'auto',
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }
    return None


def update_conversation(user_id: str, conversation_id: str, title: str = None, 
                        model_id: str = None, reasoning_effort: str = None) -> dict:
    """Update a conversation."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    
    if model_id is not None:
        updates.append("model_id = ?")
        params.append(model_id)
    
    if reasoning_effort is not None:
        updates.append("reasoning_effort = ?")
        params.append(reasoning_effort)
    
    updates.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(conversation_id)
    
    cursor.execute(f'''
        UPDATE conversations 
        SET {", ".join(updates)}
        WHERE id = ?
    ''', params)
    
    conn.commit()
    conn.close()
    
    return get_conversation(user_id, conversation_id)


def delete_conversation(user_id: str, conversation_id: str) -> bool:
    """Delete a conversation and its messages."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    # Delete messages first
    cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
    
    # Delete conversation
    cursor.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
    
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    
    return deleted


def add_message(user_id: str, conversation_id: str, role: str, content: str, 
                tool_calls: list = None, tool_call_id: str = None) -> dict:
    """Add a message to a conversation."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    message_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    tool_calls_json = json.dumps(tool_calls) if tool_calls else None
    
    cursor.execute('''
        INSERT INTO messages (id, conversation_id, role, content, tool_calls, tool_call_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (message_id, conversation_id, role, content, tool_calls_json, tool_call_id, now))
    
    # Update conversation updated_at
    cursor.execute('''
        UPDATE conversations SET updated_at = ? WHERE id = ?
    ''', (now, conversation_id))
    
    conn.commit()
    conn.close()
    
    return {
        'id': message_id,
        'conversation_id': conversation_id,
        'role': role,
        'content': content,
        'tool_calls': tool_calls,
        'tool_call_id': tool_call_id,
        'created_at': now
    }


def get_messages(user_id: str, conversation_id: str) -> list:
    """Get all messages in a conversation."""
    conn = get_user_db(user_id)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, conversation_id, role, content, tool_calls, tool_call_id, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
    ''', (conversation_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        tool_calls = json.loads(row['tool_calls']) if row['tool_calls'] else None
        messages.append({
            'id': row['id'],
            'conversation_id': row['conversation_id'],
            'role': row['role'],
            'content': row['content'],
            'tool_calls': tool_calls,
            'tool_call_id': row['tool_call_id'],
            'created_at': row['created_at']
        })
    
    return messages


def get_messages_for_llm(user_id: str, conversation_id: str) -> list:
    """Get messages formatted for LLM API call."""
    messages = get_messages(user_id, conversation_id)
    
    llm_messages = []
    for msg in messages:
        message = {"role": msg['role'], "content": msg['content']}
        
        if msg['tool_calls']:
            message['tool_calls'] = msg['tool_calls']
        
        if msg['tool_call_id']:
            message['tool_call_id'] = msg['tool_call_id']
        
        llm_messages.append(message)
    
    return llm_messages
