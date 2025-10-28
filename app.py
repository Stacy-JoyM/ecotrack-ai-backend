
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
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-this'  # Change this too
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # Token expires in 24 hours
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    
    db.init_app(app)
    migrate.init_app(app, db)
     # Initialize extensions
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    jwt.init_app(app)
    bcrypt.init_app(app) 
    logging.basicConfig(level=logging.INFO)
    
    with app.app_context():
        db.create_all()
        

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
    app = create_app()
    app.run(debug=True)