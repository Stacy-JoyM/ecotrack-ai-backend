from flask import Blueprint, request, jsonify
import os
import json
from services.discover_service import geocode_place, find_nearby_recycling_centers
from utils import haversine_distance
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="ecotrack-ai-application")

discover_bp = Blueprint('discover_bp', __name__, url_prefix='/api')

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
PLACES_FILE = os.path.join(DATA_DIR, 'places.json')

try:
    with open(PLACES_FILE) as f:
        ALL_PLACES = json.load(f)
except FileNotFoundError:
    ALL_PLACES = []

@discover_bp.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'Discover blueprint is up'}), 200

@discover_bp.route('/geocode', methods=['GET'])
def geocode():
    place = request.args.get('place', '').strip()
    if not place:
        return jsonify({"error": "The 'place' query parameter is required."}), 400
    coords = geocode_place(place)
    if not coords:
        return jsonify({"error": "Location not found"}), 404
    return jsonify({
        "coordinates": {"lat": coords['lat'], "lng": coords['lng']},
        "place_name": coords['display_name']
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
        searchable = (place.get("name", "").lower() + " " +
                      place.get("category", "").lower() + " " +
                      " ".join(place.get("keywords", [])).lower())
        if query in searchable or not query:
            dist = haversine_distance(user_lat, user_lng, place.get("lat", 0), place.get("lng", 0))
            results.append({
                "id": place.get("id"),
                "name": place.get("name"),
                "category": place.get("category"),
                "rating": place.get("rating", 0),
                "distance_km": dist,
                "coordinates": [place.get("lng", 0), place.get("lat", 0)]
            })

    if not results and query:
        coords = geocode_place(query)
        if coords:
            results.append({
                "id": 0,
                "name": coords['display_name'],
                "category": "Unknown",
                "rating": 0,
                "distance_km": 0,
                "coordinates": [coords['lng'], coords['lat']]
            })

    results.sort(key=lambda x: x["distance_km"])
    return jsonify(results)

@discover_bp.route('/places/fallback', methods=['GET'])
def fallback_places():
    if ALL_PLACES:
        return jsonify({"message": "Places data exists"}), 200
    else:
        return jsonify([{
            "id": 0,
            "name": "Default Park",
            "category": "Park",
            "rating": 5,
            "distance_km": 0,
            "coordinates": [0, 0]
        }])
    

@discover_bp.route('/api/discover/reverse', methods=['GET'])
def reverse_geocode():
    """Convert coordinates to place name"""
    lng = request.args.get('lng')
    lat = request.args.get('lat')
    
    if not lng or not lat:
        return jsonify({'error': 'Longitude and latitude parameters are required'}), 400
    
    try:
        # Reverse geocode: coordinates to place name
        location = geolocator.reverse(f"{lat}, {lng}")
        
        if location:
            return jsonify({
                'place_name': location.address,
                'coordinates': [float(lng), float(lat)]
            })
        else:
            return jsonify({'error': 'Location not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500