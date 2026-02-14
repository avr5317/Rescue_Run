import os
import json
import httpx
from typing import Optional

from app.llm.prompts import SYSTEM_PROMPT

def get_api_key() -> Optional[str]:
    """Get Gemini API key from environment."""
    return os.getenv("GEMINI_API_KEY")

def get_model_name() -> str:
    """Get Gemini model name from environment."""
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def extract_json_from_response(text: str) -> dict:
    """
    Extract JSON object from Gemini response.
    Gemini sometimes returns extra text, this pulls the first top-level {...} block.
    """
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")
    candidate = text[start:end+1]
    return json.loads(candidate)

async def call_gemini(prompt: str) -> dict:
    """
    Call Gemini API with the provided prompt.
    Returns the parsed response data.
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")
    
    model_name = get_model_name()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json"
    }

    # Combine system and user prompts
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser text:\n{prompt}\n\nReturn ONLY the JSON object."

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": full_prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2
        }
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()

    # Extract text from Gemini response structure
    try:
        content_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return extract_json_from_response(content_text)
    except Exception as e:
        raise ValueError(f"Failed to extract content from Gemini response: {e}")
