"""
Authentication routes.
"""

from flask import Blueprint, request, jsonify, g
from app.models.user import create_user, verify_user, get_user_by_id
from app.utils.auth import generate_token, token_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with username and password."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '未提供数据'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    user = verify_user(username, password)
    
    if not user:
        return jsonify({'error': '用户名或密码错误'}), 401
    
    token = generate_token(user['id'], user['is_admin'])
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'is_admin': user['is_admin']
        }
    })


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '未提供数据'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    if len(username) < 3:
        return jsonify({'error': '用户名至少需要3个字符'}), 400
    
    if len(password) < 6:
        return jsonify({'error': '密码至少需要6个字符'}), 400
    
    user = create_user(username, password)
    
    if not user:
        return jsonify({'error': '用户名已存在'}), 409
    
    token = generate_token(user['id'], user['is_admin'])
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'is_admin': user['is_admin']
        }
    }), 201


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user info."""
    return jsonify({
        'user': g.user
    })


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change user password."""
    from app.models.user import get_users_db, hash_password
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '未提供数据'}), 400
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': '旧密码和新密码不能为空'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': '新密码至少需要6个字符'}), 400
    
    conn = get_users_db()
    cursor = conn.cursor()
    
    old_hash = hash_password(old_password)
    cursor.execute('SELECT id FROM users WHERE id = ? AND password_hash = ?', 
                   (g.user_id, old_hash))
    
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': '当前密码不正确'}), 401
    
    new_hash = hash_password(new_password)
    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                   (new_hash, g.user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': '密码修改成功'})
