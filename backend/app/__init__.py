"""
Flask application factory.
"""

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import sys

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config.JWT_ACCESS_TOKEN_EXPIRES
    
    # Enable CORS
    CORS(app, origins=config.CORS_ORIGINS, supports_credentials=True)
    
    # Ensure data directories exist
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.USER_DATA_DIR, exist_ok=True)
    
    # Initialize database
    from app.models.user import init_users_db
    init_users_db()
    
    # Initialize models config
    from app.models.model_config import init_models_config
    init_models_config()
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.chat import chat_bp
    from app.routes.admin import admin_bp
    from app.routes.models import models_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(models_bp, url_prefix='/api/models')
    
    # Initialize SocketIO
    socketio.init_app(app)
    
    # Register SocketIO events
    from app.routes import chat_socket
    
    return app
