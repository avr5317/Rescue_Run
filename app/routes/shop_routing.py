from fastapi import APIRouter, HTTPException
from bson import ObjectId
from typing import List, Dict, Any

from app.db import requests_col
from app.models import LatLng
from app.llm.google_places_client import find_shop_location
from app.llm.distance_calculator import haversine_distance, generate_navigation_link, sort_shops_by_distance


router = APIRouter()


@router.post("/requests/{request_id}/find-shops")
async def find_nearest_shops(request_id: str, user_location: LatLng):
    """
    Find nearest physical shop locations for each item in the request.
    Returns navigation links for each item's nearest shop.
    
    Args:
        request_id: MongoDB ObjectId of the request
        user_location: User's current location
        
    Returns:
        {
            "items": [
                {
                    "item_name": "painkillers",
                    "nearest_shop": {...},
                    "all_shops_sorted": [...]
                }
            ],
            "navigation_links": {...}
        }
    """
    print(f"[ShopRouting] Finding shops for request {request_id} at ({user_location.lat}, {user_location.lng})")
    
    # Fetch request from database
    try:
        request_doc = requests_col.find_one({"_id": ObjectId(request_id)})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request ID: {e}")
    
    if not request_doc:
        raise HTTPException(status_code=404, detail="Request not found")
    
    items = request_doc.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="Request has no items")
    
    result_items = []
    navigation_links = {}
    
    # Process each item independently
    for idx, item in enumerate(items):
        item_name = item.get("name", "")
        shops = item.get("shops", [])
        shop_prices = item.get("shop_prices", [])
        
        if not shops or not shop_prices:
            print(f"[ShopRouting] No shops found for item '{item_name}', skipping")
            continue
        
        print(f"[ShopRouting] Processing item '{item_name}' with {len(shops)} shops")
        
        # Find location for each shop
        shop_locations = []
        for shop_price in shop_prices:
            shop_name = shop_price.get("shop", "")
            price = shop_price.get("price", 0.0)
            
            # Find physical location via Google Places API
            location = await find_shop_location(
                shop_name,
                user_location.lat,
                user_location.lng
            )
            
            if location:
                shop_locations.append({
                    "shop": shop_name,
                    "price": price,
                    "name": location["name"],
                    "address": location["address"],
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "place_id": location["place_id"]
                })
        
        if not shop_locations:
            print(f"[ShopRouting] No physical locations found for item '{item_name}'")
            continue
        
        # Calculate distances and sort
        sorted_shops = sort_shops_by_distance(
            shop_locations,
            user_location.lat,
            user_location.lng
        )
        
        # Add navigation links
        for shop in sorted_shops:
            shop["navigation_link"] = generate_navigation_link(shop["lat"], shop["lng"])
        
        # Get nearest shop (first after sorting)
        nearest = sorted_shops[0]
        
        print(f"[ShopRouting] Nearest shop for '{item_name}': {nearest['shop']} ({nearest['distance_mi']:.2f} mi)")
        
        result_items.append({
            "item_name": item_name,
            "nearest_shop": nearest,
            "all_shops_sorted": sorted_shops
        })
        
        # Add to navigation links dict
        navigation_links[f"item_{idx + 1}_{item_name}"] = nearest["navigation_link"]
    
    # Add request location link
    navigation_links["request_location"] = f"https://www.google.com/maps?q={user_location.lat},{user_location.lng}"
    
    return {
        "items": result_items,
        "navigation_links": navigation_links
    }
