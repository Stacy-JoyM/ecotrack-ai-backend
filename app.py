from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
import os
from datetime import timedelta
import logging
from extensions import bcrypt

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name=None):
    if config_name is None:
        # Default to 'production' if not explicitly set, common for deployment servers
        config_name = os.getenv('FLASK_ENV', 'production')
    
    app = Flask(__name__)
    
    # 1. Load configuration from config[config_name] (which should include secret keys and database URI)
    app.config.from_object(config[config_name])
    
    # Configuration Overrides/Additions
    # Removed: app.config['JWT_SECRET_KEY'] = '...' (Rely on environment variable in config.py)
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    # Removed: app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') (Rely on config[config_name] to prevent double-setting)
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize extensions
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000", os.getenv('CORS_ORIGIN', '*')],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    jwt.init_app(app)
    bcrypt.init_app(app) 
    logging.basicConfig(level=logging.INFO)
    
    with app.app_context():
        # *** CRITICAL CHANGE: Removed db.create_all() for production use.
        # Database schema management is now handled entirely by 'flask db upgrade' 
        # run via the Render Build Command.
        pass 
        
    from routes import register_blueprints
    register_blueprints(app)

    
    @app.route('/')
    def index():
       return jsonify({
        'message': 'Carbon Footprint Tracker API',
        'version': '1.0',
        'endpoints': {
            'activity': '/api/activity',
            'carbon': '/api/carbon',
            'chatbot': '/api/chatbot',
            'dashboard': '/api/dashboard',
            'discover': '/api/discover',
            'user': '/api/user',

        }
       })

    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Backend is running'}, 200
    
    return app

if __name__ == '__main__':
    # When running locally, ensure FLASK_ENV is set to 'development' or 'local' 
    # if you want different behavior than the default 'production'.
    app = create_app()
    app.run(debug=True)
