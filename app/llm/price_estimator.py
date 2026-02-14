import json
from typing import Dict, Any, List
from app.llm.client import get_api_key
from app.llm.serpapi_client import fetch_shops_for_items
import google.generativeai as genai


PRICE_ESTIMATOR_PROMPT = """You are a price estimation assistant for a crisis mutual-aid app.

Analyze the request and:
1. Determine if it's for physical ITEMS or a SERVICE
2. If ITEMS: You don't need to estimate price (will be done via product search)
3. If SERVICE: Estimate a realistic price for the service

ITEMS examples: groceries, medicines, food, supplies, physical goods
SERVICE examples: rides, transport, shelter rental, professional services, labor

Return ONLY JSON:
{
  "type": "items" | "service",
  "estimated_total": number (only if service, otherwise 0),
  "confidence": 0.0-1.0
}

Rules:
- estimated_total should be between 5 and 250
- Be conservative and realistic
- For items, set estimated_total to 0
- For services, estimate based on typical costs in the US

Return JSON only. No markdown. No extra text.
"""


async def classify_and_estimate(text: str) -> Dict[str, Any]:
    """
    Use LLM to classify request as items vs service and estimate price for services.
    
    Returns:
        {
            "type": "items" | "service",
            "estimated_total": float,
            "confidence": float
        }
    """
    api_key = get_api_key()
    if not api_key:
        # Fallback: assume items with 0 estimate
        return {"type": "items", "estimated_total": 0.0, "confidence": 0.3}
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        response = model.generate_content(
            f"{PRICE_ESTIMATOR_PROMPT}\n\nUser request: {text}",
            generation_config={"temperature": 0.3}
        )
        
        raw_text = response.text.strip()
        # Remove markdown code blocks if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        
        result = json.loads(raw_text)
        
        return {
            "type": result.get("type", "items"),
            "estimated_total": float(result.get("estimated_total", 0.0)),
            "confidence": float(result.get("confidence", 0.7))
        }
    
    except Exception as e:
        print(f"Price estimator LLM error: {e}")
        # Fallback: assume items
        return {"type": "items", "estimated_total": 0.0, "confidence": 0.3}


async def estimate_with_shops(text: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main price estimation function that:
    1. Classifies request as items vs service
    2. If items: fetches shop names and prices via SerpAPI, calculates estimated total
    3. If service: uses LLM estimate
    
    Args:
        text: User's request text
        items: List of parsed items from main intake LLM
        
    Returns:
        {
            "request_type": "items" | "service",
            "estimated_total": float,
            "items_with_shops": List[Dict] (items with shops and shop_prices fields),
            "confidence": float
        }
    """
    # Classify request type
    classification = await classify_and_estimate(text)
    print(f"[PriceEstimator] Request classified as: {classification['type']}")
    
    if classification["type"] == "items":
        # Fetch shop names and prices for each item via SerpAPI
        enriched_items = await fetch_shops_for_items(items)
        
        # Calculate estimated total from shop prices (use average price per item * quantity)
        estimated_total = 0.0
        for item in enriched_items:
            shop_prices = item.get("shop_prices", [])
            if shop_prices:
                # Get average price from available shops
                prices = [sp.get("price", 0.0) for sp in shop_prices if sp.get("price", 0.0) > 0]
                if prices:
                    avg_price = sum(prices) / len(prices)
                    qty = item.get("qty", 1)
                    estimated_total += avg_price * qty
        
        # If no prices found, set to 0
        estimated_total = round(estimated_total, 2)
        print(f"[PriceEstimator] ✅ ITEMS - Calculated estimated_total from SerpAPI: ${estimated_total}")
        
        return {
            "request_type": "items",
            "estimated_total": estimated_total,
            "items_with_shops": enriched_items,
            "confidence": classification["confidence"]
        }
    else:
        # Service - use LLM estimate
        # Add empty shops and shop_prices to items
        items_with_empty_data = [
            {**item, "shops": [], "shop_prices": []} for item in items
        ]
        
        print(f"[PriceEstimator] ✅ SERVICE - Using LLM estimate: ${classification['estimated_total']}")
        return {
            "request_type": "service",
            "estimated_total": classification["estimated_total"],
            "items_with_shops": items_with_empty_data,
            "confidence": classification["confidence"]
        }
