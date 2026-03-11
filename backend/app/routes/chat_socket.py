"""
WebSocket handlers for real-time chat.
"""

import json
import threading
from flask import request
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app.utils.auth import decode_token
from app.models.user import get_user_by_id
from app.models.conversation import (
    add_message, get_messages_for_llm, get_conversation, update_conversation
)
from app.services.llm_service import LLMService


# Store user sessions
user_sessions = {}

# Store active generation tasks: {sid: {'stop_flag': threading.Event(), 'conversation_id': str}}
active_generations = {}


def emit_and_flush(event, data, **kwargs):
    """Emit a socket event and yield control to allow it to be sent immediately."""
    emit(event, data, **kwargs)
    socketio.sleep(0)


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")
    
    # Stop any active generation for this client
    if request.sid in active_generations:
        active_generations[request.sid]['stop_flag'].set()
        del active_generations[request.sid]
        print(f"Stopped active generation for disconnected client: {request.sid}")
    
    if request.sid in user_sessions:
        del user_sessions[request.sid]


@socketio.on('authenticate')
def handle_authenticate(data):
    """Authenticate WebSocket connection with JWT token."""
    token = data.get('token')
    
    if not token:
        emit('auth_error', {'error': '未提供令牌'})
        return
    
    payload = decode_token(token)
    if not payload:
        emit('auth_error', {'error': '令牌无效或已过期'})
        return
    
    user = get_user_by_id(payload['user_id'])
    if not user:
        emit('auth_error', {'error': '用户不存在'})
        return
    
    user_sessions[request.sid] = {
        'user_id': payload['user_id'],
        'is_admin': payload.get('is_admin', False)
    }
    
    emit('authenticated', {'user_id': payload['user_id']})


@socketio.on('join_conversation')
def handle_join_conversation(data):
    """Join a conversation room."""
    if request.sid not in user_sessions:
        emit('error', {'error': '未认证'})
        return
    
    conversation_id = data.get('conversation_id')
    if conversation_id:
        join_room(conversation_id)
        emit('joined', {'conversation_id': conversation_id})


@socketio.on('leave_conversation')
def handle_leave_conversation(data):
    """Leave a conversation room."""
    conversation_id = data.get('conversation_id')
    if conversation_id:
        leave_room(conversation_id)


@socketio.on('send_message')
def handle_send_message(data):
    """Handle incoming chat message and stream response."""
    if request.sid not in user_sessions:
        emit('error', {'error': '未认证'})
        return
    
    session = user_sessions[request.sid]
    user_id = session['user_id']
    sid = request.sid
    
    conversation_id = data.get('conversation_id')
    content = data.get('content')
    model_id = data.get('model_id')
    reasoning_effort = data.get('reasoning_effort') or 'auto'
    is_regenerate = data.get('is_regenerate', False)
    
    if not conversation_id or not content:
        emit('error', {'error': '缺少对话ID或内容'})
        return
    
    # Verify conversation belongs to user
    conversation = get_conversation(user_id, conversation_id)
    if not conversation:
        emit('error', {'error': '对话不存在'})
        return
    
    # Only save user message if this is not a regeneration
    if not is_regenerate:
        user_msg = add_message(user_id, conversation_id, 'user', content)
        emit('message_saved', {'message': user_msg})
        
        # Update conversation title if it's the first message
        messages = get_messages_for_llm(user_id, conversation_id)
        if len(messages) == 1:
            title = content[:50] + '...' if len(content) > 50 else content
            update_conversation(user_id, conversation_id, title=title)
            emit('conversation_updated', {'title': title})
    
    # Use model from conversation or request
    use_model_id = model_id or conversation.get('model_id')
    
    try:
        llm_service = LLMService(use_model_id)
    except ValueError as e:
        emit('stream_error', {'error': str(e)})
        return
    
    # Prepare messages for LLM
    llm_messages = get_messages_for_llm(user_id, conversation_id)
    
    # Create stop flag for this generation
    stop_flag = threading.Event()
    active_generations[sid] = {
        'stop_flag': stop_flag,
        'conversation_id': conversation_id
    }
    
    # Stream response
    assistant_content = ""
    tool_calls_data = []
    parts_data = []
    generation_stopped = False
    
    emit_and_flush('stream_start', {})
    
    try:
        for event in llm_service.chat_with_tools(llm_messages, reasoning_effort=reasoning_effort, stop_flag=stop_flag):
            # Check if generation should be stopped
            if stop_flag.is_set():
                generation_stopped = True
                break
            
            if event['type'] == 'content':
                assistant_content += event['content']
                emit_and_flush('stream_content', {'content': event['content']})
                
                # Track content parts
                if parts_data and parts_data[-1]['type'] == 'content':
                    parts_data[-1]['text'] += event['content']
                else:
                    parts_data.append({'type': 'content', 'text': event['content']})
            
            elif event['type'] == 'tool_call_start':
                emit_and_flush('tool_call_start', {
                    'id': event['id'],
                    'tool': event['tool']
                })
                
                # Track tool call parts
                parts_data.append({
                    'type': 'tool_call',
                    'name': event['tool'],
                    'collapsed': True
                })
            
            elif event['type'] == 'tool_call_args':
                emit_and_flush('tool_call_args', {
                    'id': event['id'],
                    'args': event['args']
                })
            
            elif event['type'] == 'tool_call_end':
                tool_calls_data.append({
                    'id': event['id'],
                    'type': 'function',
                    'function': {
                        'name': event['tool'],
                        'arguments': json.dumps(event.get('arguments', {}))
                    }
                })
                emit_and_flush('tool_call_end', {
                    'id': event['id'],
                    'tool': event['tool'],
                    'result': event.get('result'),
                    'error': event.get('error')
                })
            
            elif event['type'] == 'error':
                emit('stream_error', {'error': event['message']})
                # Clean up active generation
                if sid in active_generations:
                    del active_generations[sid]
                return
        
        # Only save message if generation completed successfully
        if not generation_stopped and assistant_content:
            # Save assistant message with parts
            assistant_msg = add_message(
                user_id, 
                conversation_id, 
                'assistant', 
                assistant_content,
                tool_calls=tool_calls_data if tool_calls_data else None,
                parts=parts_data if parts_data else None
            )
            
            emit('stream_end', {'message': assistant_msg})
        elif generation_stopped:
            # Notify client that generation was stopped
            emit('stream_error', {'error': '生成已停止', 'stopped': True})
        
    except Exception as e:
        emit('stream_error', {'error': str(e)})
    finally:
        # Clean up active generation
        if sid in active_generations:
            del active_generations[sid]


@socketio.on('stop_generation')
def handle_stop_generation(data):
    """Handle request to stop generation."""
    sid = request.sid
    
    if sid in active_generations:
        active_generations[sid]['stop_flag'].set()
        print(f"Stop signal sent for generation: {sid}")
        emit('generation_stopped', {})
    else:
        emit('generation_stopped', {'message': '没有正在进行的生成'})
