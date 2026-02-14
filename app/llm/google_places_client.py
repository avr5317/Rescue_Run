import os
from typing import Dict, Any, Optional
import httpx


def get_places_api_key() -> str:
    """Get Google Places API key from environment."""
    return os.getenv("GOOGLE_PLACES_API_KEY", "")


async def find_shop_location(
    shop_name: str,
    user_lat: float,
    user_lng: float,
    radius: int = 5000
) -> Optional[Dict[str, Any]]:
    """
    Find the nearest physical location for a shop using Google Places API.
    
    Args:
        shop_name: Name of the shop (e.g., "cvs", "walmart")
        user_lat, user_lng: User's location
        radius: Search radius in meters (default 5km)
        
    Returns:
        Dict with shop details or None if not found:
        {
            "name": "CVS Pharmacy",
            "address": "123 Main St, Boston MA",
            "lat": 42.361,
            "lng": -71.062,
            "place_id": "ChIJ..."
        }
    """
    api_key = get_places_api_key()
    if not api_key or api_key == "your_google_places_api_key_here":
        print(f"[GooglePlaces] No valid API key found")
        return None
    
    try:
        # Determine place type based on shop name
        place_type = _get_place_type(shop_name)
        
        # Google Places API - Nearby Search
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{user_lat},{user_lng}",
            "radius": radius,
            "keyword": shop_name,
            "key": api_key
        }
        
        if place_type:
            params["type"] = place_type
        
        print(f"[GooglePlaces] Searching for '{shop_name}' near ({user_lat}, {user_lng})")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        
        if data.get("status") != "OK" or not data.get("results"):
            print(f"[GooglePlaces] No results found for '{shop_name}': {data.get('status')}")
            return None
        
        # Get first (nearest) result
        result = data["results"][0]
        location = result["geometry"]["location"]
        
        shop_data = {
            "name": result.get("name", shop_name),
            "address": result.get("vicinity", ""),
            "lat": location["lat"],
            "lng": location["lng"],
            "place_id": result.get("place_id", "")
        }
        
        print(f"[GooglePlaces] Found: {shop_data['name']} at {shop_data['address']}")
        return shop_data
        
    except Exception as e:
        print(f"[GooglePlaces] Error finding '{shop_name}': {e}")
        return None


def _get_place_type(shop_name: str) -> Optional[str]:
    """
    Determine Google Places type based on shop name.
    
    Returns:
        Google Places type string or None
    """
    shop_lower = shop_name.lower()
    
    # Pharmacy/drugstore
    if any(name in shop_lower for name in ["cvs", "walgreens", "rite aid", "pharmacy"]):
        return "pharmacy"
    
    # Supermarket/grocery
    if any(name in shop_lower for name in ["walmart", "target", "kroger", "safeway", "whole foods", "trader joe"]):
        return "supermarket"
    
    # Convenience store
    if any(name in shop_lower for name in ["7-eleven", "circle k", "wawa"]):
        return "convenience_store"
    
    # Default: no specific type filter
    return None
