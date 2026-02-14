from typing import Dict, Any

def clamp_and_sanitize(raw: dict) -> Dict[str, Any]:
    """Validate and sanitize AI-generated draft."""
    cat = raw.get("category", "other")
    urg = raw.get("urgency_window", "today")
    sev = int(raw.get("severity", 2))
    items = raw.get("items", []) or []
    est = float(raw.get("estimated_total", 25))

    if cat not in ["meds", "groceries", "shelter", "transport", "other"]:
        cat = "other"
    if urg not in ["now", "today", "week"]:
        urg = "today"
    sev = max(1, min(5, sev))

    fixed_items = []
    for it in items[:6]:
        name = str(it.get("name", "")).strip()[:60]
        if not name:
            continue
        fixed_items.append({
            "name": name,
            "qty": float(it.get("qty", 1)),
            "unit": str(it.get("unit", "unit"))[:30],
            "notes": str(it.get("notes", ""))[:120]
        })
    if not fixed_items:
        fixed_items = [{"name": cat, "qty": 1, "unit": "unit", "notes": ""}]

    est = round(max(5.0, min(250.0, est)), 2)

    return {
        "category": cat,
        "urgency_window": urg,
        "severity": sev,
        "items": fixed_items,
        "estimated_total": est,
        "notes": ""
    }
