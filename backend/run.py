#!/usr/bin/env python3
"""
Entry point for running the Flask application.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from app import create_app, socketio


def main():
    """Run the application."""
    app = create_app()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                      Dummy System                            ║
╠══════════════════════════════════════════════════════════════╣
║  Server running at: http://{config.SERVER_HOST}:{config.SERVER_PORT}                    ║
║  Debug mode: {str(config.DEBUG).ljust(46)}║
║                                                              ║
║  Admin credentials:                                          ║
║    Username: {config.ADMIN_USERNAME.ljust(47)}║
║    Password: {config.ADMIN_PASSWORD.ljust(47)}║
║                                                              ║
║  Change these in config.py for production!                   ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    socketio.run(
        app,
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        debug=config.DEBUG
    )


if __name__ == '__main__':
    main()
