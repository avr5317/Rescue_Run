from typing import Dict, Any
import asyncio

from app.llm.client import get_api_key, call_gemini
from app.llm.parsers import fallback_parse
from app.llm.validators import clamp_and_sanitize
from app.llm.price_estimator import estimate_with_shops

async def ai_invoke(text: str) -> Dict[str, Any]:
    """
    Main AI intake function with parallel LLM processing.
    
    Runs two LLMs concurrently:
    1. Main intake LLM: extracts category, urgency, severity, items
    2. Price estimator LLM: classifies as items/service, fetches shops via SerpAPI
    
    Returns:
        {
            "draft": {
                "category": str,
                "urgency_window": str,
                "severity": int,
                "items": List[Dict],  # with shops field
                "estimated_total": float,
                "notes": str
            },
            "confidence": float,
            "request_type": "items" | "service"  # NEW
        }
    """
    # Check if API key is available
    if not get_api_key():
        fallback_result = fallback_parse(text)
        # Add empty shops and shop_prices to items in fallback
        for item in fallback_result["draft"]["items"]:
            item["shops"] = []
            item["shop_prices"] = []
        fallback_result["request_type"] = "items"
        return fallback_result

    # Run both LLMs in parallel
    try:
        # Task 1: Main intake parsing
        intake_task = call_gemini(text)
        
        # Start both tasks
        intake_raw = await intake_task
        intake_draft = clamp_and_sanitize(intake_raw)
        
        # Task 2: Price estimation (needs items from intake)
        price_result = await estimate_with_shops(text, intake_draft.get("items", []))
        
        # Merge results
        final_draft = {
            **intake_draft,
            "items": price_result["items_with_shops"],  # Replace items with enriched version
            "estimated_total": price_result["estimated_total"],  # Always use price estimator's calculated total
        }
        
        print(f"[Intake] 🎯 Final estimated_total: ${final_draft['estimated_total']} (type: {price_result['request_type']})")
        return {
            "draft": final_draft,
            "confidence": (0.8 + price_result["confidence"]) / 2,  # Average confidence
            "request_type": price_result["request_type"]
        }
        
    except Exception as e:
        print(f"AI invoke error: {e}")
        # If anything fails, use fallback
        fallback_result = fallback_parse(text)
        for item in fallback_result["draft"]["items"]:
            item["shops"] = []
            item["shop_prices"] = []
        fallback_result["request_type"] = "items"
        return fallback_result

