import re
import random
from typing import Dict, Any, List

def guess_category(text: str) -> str:
    """Guess category from text keywords."""
    t = text.lower()
    if any(k in t for k in ["insulin", "medicine", "meds", "prescription", "pharmacy", "antibiotic", "inhaler"]):
        return "meds"
    if any(k in t for k in ["grocer", "food", "rice", "milk", "bread", "eggs", "vegetable", "grocery"]):
        return "groceries"
    if any(k in t for k in ["shelter", "evac", "no place", "homeless", "housing"]):
        return "shelter"
    if any(k in t for k in ["ride", "pickup", "drive", "car", "transport", "uber"]):
        return "transport"
    return "other"

def guess_urgency(text: str) -> str:
    """Guess urgency from text keywords."""
    t = text.lower()
    if any(k in t for k in ["asap", "urgent", "now", "immediately", "tonight"]):
        return "now"
    if any(k in t for k in ["today", "by end of day", "this evening"]):
        return "today"
    return "week"

def guess_severity(category: str, text: str) -> int:
    """Guess severity based on category and keywords."""
    t = text.lower()
    if category == "meds" and any(k in t for k in ["insulin", "oxygen", "dialysis", "heart", "seizure"]):
        return 5
    if category in ["shelter"] and any(k in t for k in ["evac", "unsafe", "flood", "fire"]):
        return 5
    if "baby" in t or "infant" in t:
        return 4
    if category == "meds":
        return 4
    return 2

def extract_items(text: str, category: str) -> List[Dict[str, Any]]:
    """Extract items from text using light heuristics."""
    t = text.strip()
    items = []
    m = re.split(r"[:\-]\s*", t, maxsplit=1)
    tail = m[1] if len(m) > 1 else t
    parts = [p.strip() for p in re.split(r",| and ", tail) if p.strip()]
    # limit to 6 items
    for p in parts[:6]:
        name = re.sub(r"[^a-zA-Z0-9\s]", "", p).strip()
        if not name:
            continue
        items.append({"name": name[:60], "qty": 1, "unit": "unit", "notes": ""})
    if not items:
        items = [{"name": category, "qty": 1, "unit": "unit", "notes": ""}]
    return items

def estimate_price(category: str, items: List[Dict[str, Any]]) -> float:
    """Generate reasonable random price estimate."""
    base = {"meds": (20, 120), "groceries": (15, 80), "shelter": (0, 60), "transport": (10, 60), "other": (10, 70)}
    lo, hi = base.get(category, (10, 70))
    # scale by item count a bit
    scale = min(1.0 + 0.15 * max(0, len(items)-1), 1.6)
    val = random.uniform(lo, hi) * scale
    return round(max(5.0, min(250.0, val)), 2)

def fallback_parse(text: str) -> Dict[str, Any]:
    """Complete fallback parsing using keyword heuristics."""
    cat = guess_category(text)
    urg = guess_urgency(text)
    sev = guess_severity(cat, text)
    items = extract_items(text, cat)
    price = estimate_price(cat, items)
    
    return {
        "draft": {
            "category": cat,
            "urgency_window": urg,
            "severity": sev,
            "items": items,
            "estimated_total": price,
            "notes": ""
        },
        "confidence": 0.55
    }
