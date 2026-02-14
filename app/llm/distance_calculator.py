import math
from typing import Tuple


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> Tuple[float, float]:
    """
    Calculate the great circle distance between two points on Earth using Haversine formula.
    
    Args:
        lat1, lng1: First point coordinates (degrees)
        lat2, lng2: Second point coordinates (degrees)
        
    Returns:
        Tuple of (distance_km, distance_mi)
    """
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance_km = R * c
    distance_mi = distance_km * 0.621371  # Convert to miles
    
    return distance_km, distance_mi


def generate_navigation_link(lat: float, lng: float) -> str:
    """
    Generate a Google Maps navigation link for the given coordinates.
    Opens Google Maps app on mobile, maps.google.com on desktop.
    
    Args:
        lat, lng: Destination coordinates
        
    Returns:
        Google Maps deep link URL
    """
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"


def sort_shops_by_distance(shops: list, user_lat: float, user_lng: float) -> list:
    """
    Sort shops by distance from user location (nearest first).
    
    Args:
        shops: List of shop dicts with 'lat' and 'lng' fields
        user_lat, user_lng: User location
        
    Returns:
        Sorted list of shops with distance_km and distance_mi added
    """
    for shop in shops:
        distance_km, distance_mi = haversine_distance(
            user_lat, user_lng,
            shop['lat'], shop['lng']
        )
        shop['distance_km'] = round(distance_km, 2)
        shop['distance_mi'] = round(distance_mi, 2)
    
    # Sort by distance (ascending)
    return sorted(shops, key=lambda s: s['distance_km'])
