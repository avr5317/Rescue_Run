import os
from typing import List, Dict, Any
from urllib.parse import urlparse
from serpapi import GoogleSearch


def get_serpapi_key() -> str:
    """Get SerpAPI key from environment."""
    return os.getenv("SERPAPI_KEY", "")


def extract_shop_data(results: Dict[str, Any]) -> tuple[List[str], List[Dict[str, Any]]]:
    """
    Extract shop names and price data from SerpAPI Google Shopping results.
    
    Returns:
        tuple: (shop_names, shop_prices)
            - shop_names: List of shop names (for backward compatibility)
            - shop_prices: List of dicts with shop, price, and link
    """
    shops = []
    shop_prices = []
    shopping_results = results.get("shopping_results", [])
    
    for product in shopping_results[:5]:  # top 5
        # SerpAPI uses 'product_link' not 'link'
        link = product.get("product_link", product.get("link", ""))
        # SerpAPI provides 'extracted_price' as float, or 'price' as string
        extracted_price = product.get("extracted_price")
        price_str = product.get("price", "")
        source = product.get("source", "")  # Shop name directly provided
        
        if not link and not source:
            continue
            
        try:
            # Get shop name from 'source' field or parse from URL
            shop_name = ""
            if source:
                # Clean up source name (remove spaces, lowercase)
                shop_name = source.lower().replace(" ", "").replace(".", "")
            elif link:
                # Parse URL and extract domain as fallback
                domain = urlparse(link).netloc
                # Remove www. prefix
                domain = domain.replace("www.", "")
                # Get the main part before first dot (e.g., "amazon" from "amazon.com")
                shop_name = domain.split(".")[0]
            
            if not shop_name or shop_name in shops:
                continue
            
            # Use extracted_price if available (already a float), else parse price string
            price = 0.0
            if extracted_price is not None:
                price = float(extracted_price)
            elif price_str:
                # Remove currency symbols and commas
                price_clean = price_str.replace("$", "").replace(",", "").strip()
                try:
                    price = float(price_clean)
                except ValueError:
                    price = 0.0
            
            shops.append(shop_name)
            shop_prices.append({
                "shop": shop_name,
                "price": price,
                "link": link if link else f"https://www.google.com/search?q={product.get('title', '')}"
            })
        except Exception as e:
            print(f"Error extracting product data: {e}")
            continue
    
    return shops, shop_prices


async def fetch_item_shops(item_name: str) -> tuple[List[str], List[Dict[str, Any]]]:
    """
    Query Google Shopping via SerpAPI to get top 10 shop names and prices for an item.
    
    Args:
        item_name: Name of the item to search for
        
    Returns:
        tuple: (shop_names, shop_prices)
    """
    print(f"[SerpAPI] Fetching prices for item: '{item_name}'")
    api_key = get_serpapi_key()
    if not api_key or api_key == "your_serpapi_key_here":
        print(f"[SerpAPI] No valid API key found, returning empty results")
        # No valid API key, return empty lists
        return [], []
    
    try:
        params = {
            "engine": "google_shopping",
            "q": item_name,
            "api_key": api_key,
            "num": 5,
            "gl": "us",  # country
            "hl": "en"   # language
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        shops, shop_prices = extract_shop_data(results)
        print(f"[SerpAPI] Found {len(shops)} shops for '{item_name}': {shops}")
        if shop_prices:
            prices = [sp['price'] for sp in shop_prices]
            print(f"[SerpAPI] Prices: ${min(prices):.2f} - ${max(prices):.2f} (avg: ${sum(prices)/len(prices):.2f})")
        return shops, shop_prices
    
    except Exception as e:
        # Log error but don't fail the request
        print(f"SerpAPI error for '{item_name}': {e}")
        return [], []


async def fetch_shops_for_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fetch shop names and prices for multiple items concurrently.
    
    Args:
        items: List of item dicts with 'name' field
        
    Returns:
        Same items list with 'shops' and 'shop_prices' fields added
    """
    import asyncio
    
    # Create tasks for all items
    tasks = [fetch_item_shops(item.get("name", "")) for item in items]
    
    # Run all searches concurrently
    results = await asyncio.gather(*tasks)
    
    # Add shops and prices to items
    enriched_items = []
    for item, (shops, shop_prices) in zip(items, results):
        enriched_item = item.copy()
        enriched_item["shops"] = shops
        enriched_item["shop_prices"] = shop_prices
        enriched_items.append(enriched_item)
    
    return enriched_items
