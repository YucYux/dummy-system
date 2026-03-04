"""
Chat routes for conversations and messages.
"""

from flask import Blueprint, request, jsonify, g
from app.models.conversation import (
    create_conversation, get_conversations, get_conversation,
    update_conversation, delete_conversation,
    add_message, get_messages
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
    
    conversation = create_conversation(g.user_id, title, model_id)
    return jsonify({'conversation': conversation}), 201


@chat_bp.route('/conversations/<conversation_id>', methods=['GET'])
@token_required
def get_single_conversation(conversation_id):
    """Get a specific conversation with messages."""
    conversation = get_conversation(g.user_id, conversation_id)
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
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
        return jsonify({'error': 'No data provided'}), 400
    
    conversation = update_conversation(
        g.user_id, 
        conversation_id,
        title=data.get('title'),
        model_id=data.get('model_id')
    )
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    return jsonify({'conversation': conversation})


@chat_bp.route('/conversations/<conversation_id>', methods=['DELETE'])
@token_required
def remove_conversation(conversation_id):
    """Delete a conversation."""
    success = delete_conversation(g.user_id, conversation_id)
    
    if not success:
        return jsonify({'error': 'Conversation not found'}), 404
    
    return jsonify({'message': 'Conversation deleted successfully'})


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
