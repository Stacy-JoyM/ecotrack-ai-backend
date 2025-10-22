from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print("Loaded MAPBOX_API_KEY:", os.getenv("MAPBOX_API_KEY"))

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    if config_name not in config:
        raise ValueError(f"Invalid config name '{config_name}'. Available: {list(config.keys())}")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    # Register blueprints
    from routes.discover_routes import discover_bp
    app.register_blueprint(discover_bp, url_prefix="/api")

    # Health check
    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy", "message": "Backend is running"}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
