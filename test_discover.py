from flask import Flask, Blueprint, request, jsonify
import requests
from flask_cors import CORS

discover_bp = Blueprint('discover', __name__)

@discover_bp.route('/api/geocode', methods=['GET'])
def geocode():
    place = request.args.get('place', 'nairobi')
    mapbox_api_key = 'sk.eyJ1Ijoic2FyYWhzdWVlIiwiYSI6ImNtZ3o3MnZ0czBibXIybHI0eXN1enZyMW0ifQ.aC2sIPH5u-yyW_20g7T3dA'
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{place}.json"
    params = {"access_token": mapbox_api_key}
    response = requests.get(url, params=params)
    return jsonify(response.json())

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
app.register_blueprint(discover_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
