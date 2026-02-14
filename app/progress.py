"""Public delivery history and timestamps, without exposing device credentials."""
from datetime import datetime, timezone


def utc_time(value):
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return None


def public_history(doc):
    history = [
        {"status": event["status"], "at": utc_time(event.get("at"))}
        for event in (doc.get("status_history") or [])
        if isinstance(event, dict) and event.get("status")
    ]
    recorded = {event["status"] for event in history}
    # Older records have creation/claim times but no transition log. Do not
    # pretend their updated_at proves when delivery or funding occurred.
    if "open" not in recorded and doc.get("created_at"):
        history.insert(0, {"status": "open", "at": utc_time(doc["created_at"])})
    claim = doc.get("claim") or {}
    if "claimed" not in recorded and claim.get("claimed_at"):
        history.append({"status": "claimed", "at": utc_time(claim["claimed_at"])})
    if not any(event["status"] == doc["status"] for event in history):
        history.append({"status": doc["status"], "at": None})
    return sorted(history, key=lambda event: event["at"] or datetime.max.replace(tzinfo=timezone.utc))


def progress_fields(doc, device=None):
    claim = doc.get("claim") or {}
    return {
        "created_at": utc_time(doc.get("created_at")),
        "updated_at": utc_time(doc.get("updated_at") or doc.get("created_at")),
        "status_history": public_history(doc),
        # helper_id is the existing bearer device token, not a public user ID.
        "claim": {"claimed_at": utc_time(claim.get("claimed_at"))} if claim else None,
        "is_claiming_helper": bool(device and claim.get("helper_id") == device),
    }
