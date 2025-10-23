from flask import Blueprint, request, jsonify
import os
import json
from services.discover_service import geocode_place
from utils import haversine_distance

discover_bp = Blueprint('discover', __name__)

@discover_bp.route('/')
def health():
    return {'status': 'discover routes placeholder'}

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
PLACES_FILE = os.path.join(DATA_DIR, 'places.json')

if os.path.exists(PLACES_FILE):
    with open(PLACES_FILE) as f:
        ALL_PLACES = json.load(f)
else:
    ALL_PLACES = []
    print("⚠️ Warning: data/places.json not found. /search will return empty results.")

@discover_bp.route('/geocode', methods=['GET'])
def geocode():
    place = request.args.get('place', '').strip()
    if not place:
        return jsonify({"error": "The 'place' query parameter is required."}), 400

    coords = geocode_place(place)
    if not coords:
        return jsonify({"error": "Location not found or geocoding failed."}), 404

    return jsonify({
        "coordinates": coords,
        "place_name": place
    })

@discover_bp.route('/search', methods=['GET'])
def search_places():
    query = request.args.get('q', '').lower().strip()
    user_lat = request.args.get('lat', type=float)
    user_lng = request.args.get('lng', type=float)

    if user_lat is None or user_lng is None:
        return jsonify({"error": "User coordinates (lat, lng) are required"}), 400

    results = []
    for place in ALL_PLACES:
        match = False
        if not query:
            match = True
        else:
            searchable = (
                place["name"].lower() +
                " " + place["category"].lower() +
                " " + " ".join(place.get("keywords", []))
            )
            if query in searchable:
                match = True

        if match:
            dist = haversine_distance(user_lat, user_lng, place["lat"], place["lng"])
            results.append({
                "id": place["id"],
                "name": place["name"],
                "category": place["category"],
                "rating": place["rating"],
                "distance_km": dist,
                "coordinates": [place["lng"], place["lat"]]
            })

    results.sort(key=lambda x: x["distance_km"])
    return jsonify(results)