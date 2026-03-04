"""
Admin routes for user management.
"""

from flask import Blueprint, request, jsonify, g
from app.models.user import get_all_users, delete_user, create_user
from app.utils.auth import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """Get all users."""
    users = get_all_users()
    return jsonify({'users': users})


@admin_bp.route('/users', methods=['POST'])
@admin_required
def add_user():
    """Create a new user (admin)."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '未提供数据'}), 400
    
    username = data.get('username')
    password = data.get('password')
    is_admin = data.get('is_admin', False)
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    user = create_user(username, password, is_admin=is_admin)
    
    if not user:
        return jsonify({'error': '用户名已存在'}), 409
    
    return jsonify({'user': user}), 201


@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def remove_user(user_id):
    """Delete a user."""
    if user_id == g.user_id:
        return jsonify({'error': '不能删除自己'}), 400
    
    success = delete_user(user_id)
    
    if not success:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({'message': '用户删除成功'})
