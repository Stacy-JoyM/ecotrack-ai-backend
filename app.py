from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    """Factory function to create and configure the Flask app."""
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'supersecretkey')
    app.config['SESSION_TYPE'] = 'filesystem'

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    # Import and register blueprints
    from routes.user_routes import user_bp
    # Later we’ll add: from routes.activity_routes import activity_bp, etc.

    app.register_blueprint(user_bp, url_prefix='/api/users')

    # Health check route
    @app.route('/')
    def home():
        return jsonify({
            "message": "Backend running successfully ✅",
            "status": "ok"
        }), 200

    return app


# For running directly
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
