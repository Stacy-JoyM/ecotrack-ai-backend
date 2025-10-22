# services/discover.py
import os
import requests
import urllib.parse
import logging
from dotenv import load_dotenv

# Load .env from project root (one level up)
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

# Optional: log once on import for debugging
# print("Loaded MAPBOX_API_KEY in service:", os.getenv("MAPBOX_API_KEY"))

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def geocode_place(place: str, mapbox_api_key: str = None, country: str = "KE") -> list:
    """
    Geocodes a place name using Mapbox Geocoding API.
    
    Args:
        place (str): The place name to geocode (e.g., "Kisumu").
        mapbox_api_key (str, optional): Mapbox public access token.
        country (str): ISO 3166-1 alpha-2 country code to bias results (default: "KE").

    Returns:
        list: [longitude, latitude] if found, else empty list.
    """
    # Use env var if no key provided
    if mapbox_api_key is None:
        mapbox_api_key = os.getenv("MAPBOX_API_KEY")
        if not mapbox_api_key:
            logger.error("MAPBOX_API_KEY is not set in environment.")
            return []

    # ✅ CRITICAL FIX: Remove extra spaces in URL
    encoded_place = urllib.parse.quote(place.strip(), safe='')
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_place}.json"

    params = {
        "access_token": mapbox_api_key,
        "country": country,
        "limit": 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        features = data.get("features", [])
        if not features:
            logger.warning(f"No geocoding results for place: '{place}'")
            return []

        # Mapbox returns [longitude, latitude]
        coordinates = features[0]["geometry"]["coordinates"]
        logger.info(f"Geocoded '{place}' → {coordinates}")
        return coordinates

    except requests.exceptions.Timeout:
        logger.error(f"Timeout while geocoding '{place}'")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {response.status_code} for '{place}': {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for '{place}': {e}")
    except ValueError as e:
        logger.error(f"Invalid JSON response for '{place}': {e}")
    except Exception as e:
        logger.error(f"Unexpected error geocoding '{place}': {e}")

    return []