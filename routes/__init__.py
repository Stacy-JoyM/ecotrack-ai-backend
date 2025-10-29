from routes.user_routes import user_bp
from routes.discover_routes import discover_bp
#from routes.dashboard_routes import dashboard_bp
from routes.activity_routes import activity_bp
from routes.chatbot_routes import chatbot_bp


def register_blueprints(app):
    
    # Register blueprints with URL prefixes
    app.register_blueprint(activity_bp, url_prefix='/api/activity')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
    #app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(discover_bp, url_prefix='/api/discover')
    app.register_blueprint(user_bp, url_prefix='/api/user')