def register_blueprints(app):
    from routes.discover_routes import discover_bp
    from routes.activity_routes import activity_bp
    # Import only existing routes

    app.register_blueprint(discover_bp, url_prefix="/api/discover")
    app.register_blueprint(activity_bp, url_prefix="/api/activities")

    # from routes.carbon_routes import carbon_bp
    # app.register_blueprint(carbon_bp, url_prefix="/api/carbon")

    # from routes.dashboard_routes import dashboard_bp
    # app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
