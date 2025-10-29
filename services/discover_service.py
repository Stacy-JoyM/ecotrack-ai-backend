from models.discover import Discover
from utils import haversine_distance

def geocode_place(place_name):
    if not place_name or not isinstance(place_name, str):
        return None
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="EcoTrack-AI/1.0")
    try:
        location = geolocator.geocode(place_name, timeout=10)
        if location:
            return {
                'lat': location.latitude,
                'lng': location.longitude,
                'display_name': location.address
            }
        return None
    except Exception as e:
        print(f"Geocoding error for '{place_name}': {e}")
        return None

def find_nearby_recycling_centers(lat, lng, radius_km=5):
    if lat is None or lng is None:
        return []

    centers = Discover.query.all()
    nearby = []

    for center in centers:
        dist = haversine_distance(lat, lng, center.latitude, center.longitude)
        if dist <= radius_km:
            nearby.append({
                'id': center.id,
                'name': center.name,
                'address': center.address,
                'latitude': center.latitude,
                'longitude': center.longitude,
                'distance_km': dist
            })

    nearby.sort(key=lambda x: x['distance_km'])
    return nearby
