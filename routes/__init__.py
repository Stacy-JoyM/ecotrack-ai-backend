from routes.user_routes import user_bp
from routes.discover_routes import discover_bp
from routes.carbon_routes import carbon_bp
from routes.dashboard_routes import dashboard_bp
from routes.activity_routes import activity_bp

def register_blueprints(app):
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(discover_bp, url_prefix='/api/discover')
    app.register_blueprint(carbon_bp, url_prefix='/api/carbon')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(activity_bp, url_prefix='/api/activities')
