
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
import os

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    jwt.init_app(app)
    
    # Import models to ensure they're registered with SQLAlchemy
    # This must be done after db.init_app() but before registering blueprints
    with app.app_context():
        import models.chat  # Import chat models
    
    # Register blueprints
    from routes import register_blueprints
    register_blueprints(app)
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Backend is running'}, 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)