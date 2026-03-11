"""
Chat routes for conversations and messages.
"""

from flask import Blueprint, request, jsonify, g
from app.models.conversation import (
    create_conversation, get_conversations, get_conversation,
    update_conversation, delete_conversation,
    add_message, get_messages, delete_message, delete_messages_from,
    get_message_by_id
)
from app.utils.auth import token_required

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/conversations', methods=['GET'])
@token_required
def list_conversations():
    """Get all conversations for current user."""
    conversations = get_conversations(g.user_id)
    return jsonify({'conversations': conversations})


@chat_bp.route('/conversations', methods=['POST'])
@token_required
def new_conversation():
    """Create a new conversation."""
    data = request.get_json() or {}
    
    title = data.get('title', 'New Chat')
    model_id = data.get('model_id')
    reasoning_effort = data.get('reasoning_effort', 'auto')
    
    conversation = create_conversation(g.user_id, title, model_id, reasoning_effort)
    return jsonify({'conversation': conversation}), 201


@chat_bp.route('/conversations/<conversation_id>', methods=['GET'])
@token_required
def get_single_conversation(conversation_id):
    """Get a specific conversation with messages."""
    conversation = get_conversation(g.user_id, conversation_id)
    
    if not conversation:
        return jsonify({'error': '对话不存在'}), 404
    
    messages = get_messages(g.user_id, conversation_id)
    
    return jsonify({
        'conversation': conversation,
        'messages': messages
    })


@chat_bp.route('/conversations/<conversation_id>', methods=['PUT'])
@token_required
def edit_conversation(conversation_id):
    """Update a conversation."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '未提供数据'}), 400
    
    conversation = update_conversation(
        g.user_id, 
        conversation_id,
        title=data.get('title'),
        model_id=data.get('model_id'),
        reasoning_effort=data.get('reasoning_effort')
    )
    
    if not conversation:
        return jsonify({'error': '对话不存在'}), 404
    
    return jsonify({'conversation': conversation})


@chat_bp.route('/conversations/<conversation_id>', methods=['DELETE'])
@token_required
def remove_conversation(conversation_id):
    """Delete a conversation."""
    success = delete_conversation(g.user_id, conversation_id)
    
    if not success:
        return jsonify({'error': '对话不存在'}), 404
    
    return jsonify({'message': '对话删除成功'})


@chat_bp.route('/tools', methods=['GET'])
@token_required
def list_tools():
    """Get available tools."""
    from app.tools import get_tool_names, get_tools_for_llm
    
    tools = get_tools_for_llm()
    tool_list = []
    
    for tool in tools:
        func = tool['function']
        tool_list.append({
            'name': func['name'],
            'description': func['description']
        })
    
    return jsonify({'tools': tool_list})


@chat_bp.route('/conversations/<conversation_id>/messages/<message_id>/regenerate', methods=['POST'])
@token_required
def regenerate_message(conversation_id, message_id):
    """
    Delete an assistant message to prepare for regeneration.
    The frontend will re-send the request via WebSocket after this.
    """
    # Verify the message exists and is an assistant message
    message = get_message_by_id(g.user_id, conversation_id, message_id)
    
    if not message:
        return jsonify({'error': '消息不存在'}), 404
    
    if message['role'] != 'assistant':
        return jsonify({'error': '只能重新生成助手消息'}), 400
    
    # Delete the assistant message
    success = delete_message(g.user_id, conversation_id, message_id)
    
    if not success:
        return jsonify({'error': '删除消息失败'}), 500
    
    return jsonify({
        'success': True,
        'message': '消息已删除，准备重新生成'
    })


@chat_bp.route('/conversations/<conversation_id>/messages/<message_id>/revert', methods=['POST'])
@token_required
def revert_to_message(conversation_id, message_id):
    """
    Delete a user message and all subsequent messages.
    Returns the content of the deleted message for filling in the input.
    """
    # Verify the message exists and is a user message
    message = get_message_by_id(g.user_id, conversation_id, message_id)
    
    if not message:
        return jsonify({'error': '消息不存在'}), 404
    
    if message['role'] != 'user':
        return jsonify({'error': '只能返回到用户消息'}), 400
    
    # Delete this message and all subsequent messages
    deleted_count = delete_messages_from(g.user_id, conversation_id, message_id)
    
    if deleted_count == 0:
        return jsonify({'error': '删除消息失败'}), 500
    
    return jsonify({
        'success': True,
        'deleted_count': deleted_count,
        'content': message['content']
    })
