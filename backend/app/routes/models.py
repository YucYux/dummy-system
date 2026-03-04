"""
Model configuration routes.
"""

from flask import Blueprint, request, jsonify
from app.models.model_config import (
    get_all_models, get_enabled_models, get_model_by_id,
    add_model, update_model, delete_model
)
from app.utils.auth import token_required, admin_required

models_bp = Blueprint('models', __name__)


@models_bp.route('/', methods=['GET'])
@token_required
def list_models():
    """Get available models for users (only enabled ones)."""
    models = get_enabled_models()
    # Hide API keys from response
    safe_models = []
    for m in models:
        safe_models.append({
            'id': m['id'],
            'name': m['name'],
            'provider': m['provider'],
            'is_default': m.get('is_default', False),
            'is_reasoning': m.get('is_reasoning', False)
        })
    return jsonify({'models': safe_models})


@models_bp.route('/admin', methods=['GET'])
@admin_required
def list_all_models():
    """Get all models for admin (including disabled and API keys)."""
    models = get_all_models()
    return jsonify({'models': models})


@models_bp.route('/admin', methods=['POST'])
@admin_required
def create_model():
    """Add a new model configuration."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '未提供数据'}), 400
    
    model = add_model(data)
    return jsonify({'model': model}), 201


@models_bp.route('/admin/<model_id>', methods=['PUT'])
@admin_required
def edit_model(model_id):
    """Update a model configuration."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '未提供数据'}), 400
    
    model = update_model(model_id, data)
    
    if not model:
        return jsonify({'error': '模型不存在'}), 404
    
    return jsonify({'model': model})


@models_bp.route('/admin/<model_id>', methods=['DELETE'])
@admin_required
def remove_model(model_id):
    """Delete a model configuration."""
    success = delete_model(model_id)
    
    if not success:
        return jsonify({'error': '模型不存在'}), 404
    
    return jsonify({'message': '模型删除成功'})
