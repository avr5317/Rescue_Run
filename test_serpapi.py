#!/usr/bin/env python
"""Test script for SerpAPI integration"""
import asyncio
import sys
sys.path.insert(0, '/Users/ackshay/Desktop/PersonalProjects/Innovaite/RescueRun')

from dotenv import load_dotenv
load_dotenv()

from app.llm.serpapi_client import fetch_item_shops, get_serpapi_key

async def test_serpapi():
    print("Testing SerpAPI integration...")
    print(f"API Key exists: {bool(get_serpapi_key())}")
    print(f"API Key (first 20 chars): {get_serpapi_key()[:20]}...")
    
    print("\nFetching prices for 'tomatoes'...")
    try:
        from serpapi import GoogleSearch
        import os
        
        params = {
            "engine": "google_shopping",
            "q": "tomatoes",
            "api_key": get_serpapi_key(),
            "num": 10,
            "gl": "us",
            "hl": "en"
        }
        
        print(f"Calling SerpAPI with params: {params['q']}")
        search = GoogleSearch(params)
        results = search.get_dict()
        
        print(f"Results keys: {results.keys()}")
        print(f"Shopping results count: {len(results.get('shopping_results', []))}")
        
        if 'error' in results:
            print(f"ERROR: {results['error']}")
        
        # Debug: print first result to see structure
        if results.get('shopping_results'):
            print(f"\nFirst result structure:")
            first = results['shopping_results'][0]
            print(f"  Keys: {first.keys()}")
            print(f"  Link: {first.get('link', 'NO LINK')}")
            print(f"  Price: {first.get('price', 'NO PRICE')}")
            print(f"  Extracted price: {first.get('extracted_price', 'NO EXTRACTED_PRICE')}")
        
        # Now call our function
        shops, shop_prices = await fetch_item_shops("tomatoes")
        
        print(f"\nShops found: {len(shops)}")
        print(f"Shops: {shops}")
        print(f"\nPrices found: {len(shop_prices)}")
        for sp in shop_prices[:3]:  # Show first 3
            print(f"  - {sp['shop']}: ${sp['price']}")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_serpapi())
