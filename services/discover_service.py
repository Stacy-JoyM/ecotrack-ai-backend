import requests

def geocode_place(place_name):
    """
    Geocode a place name to latitude and longitude using OpenStreetMap Nominatim.
    """
    if not place_name or not isinstance(place_name, str):
        return None

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': place_name.strip(),
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'EcoTrack-AI/1.0 (contact: your-email@example.com)' 
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data and isinstance(data, list) and len(data) > 0:
            return {
                'lat': float(data[0]['lat']),
                'lng': float(data[0]['lon']),
                'display_name': data[0]['display_name']
            }
        return None
    except Exception as e:
        print(f"Geocoding error for '{place_name}': {e}")
        return None

def find_nearby_recycling_centers(lat, lng, radius_km=5):
    return []