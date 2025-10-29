from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
from extensions import bcrypt, db, migrate, jwt
from routes import register_blueprints
import os
from datetime import timedelta

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-this'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    if not app.config['OPENAI_API_KEY']:
        raise RuntimeError("OPENAI_API_KEY not set in environment!")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)

    CORS(app, origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ], supports_credentials=True)

    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        return response

    register_blueprints(app)

    @app.route('/')
    def index():
        return jsonify({
            'message': 'Carbon Footprint Tracker API',
            'version': '1.0',
            'endpoints': {
                'geocode': '/api/discover/geocode'
            }
        })

    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Backend is running'}), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
