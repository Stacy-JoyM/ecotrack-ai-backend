from flask import Flask
from routes.discover_routes import discover_bp

app = Flask(__name__)
app.config['MAPBOX_API_KEY'] = 'your_mapbox_api_key_here'  
app.register_blueprint(discover_bp)

if __name__ == "__main__":
    app.run(debug=True)
