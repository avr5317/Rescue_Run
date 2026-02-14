from datetime import datetime, timezone

def _as_utc(dt: datetime) -> datetime:
    # PyMongo commonly returns naive UTC datetimes; normalize before arithmetic.
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def compute_funding_goal(estimated_total: float, requester_afford: float) -> float:
    return max(round(estimated_total - requester_afford, 2), 0.0)

def progress_ratio(funded: float, goal: float) -> float:
    if goal <= 0:
        return 1.0
    return max(0.0, min(1.0, funded / goal))

def urgency_weight(urgency: str) -> float:
    return {"now": 1.0, "today": 0.7, "week": 0.3}[urgency]

def severity_weight(sev: int) -> float:
    return (sev - 1) / 4  # 1..5 -> 0..1

def age_hours(created_at) -> float:
    now = datetime.now(timezone.utc)
    delta = now - _as_utc(created_at)
    return max(0.0, delta.total_seconds() / 3600.0)

def rank_score(urgency: str, severity: int, progress: float, created_at) -> float:
    # deterministic + explainable:
    # more urgent + more severe + less funded + older => higher
    u = urgency_weight(urgency)
    s = severity_weight(severity)
    gap = 1.0 - progress
    a = min(1.0, age_hours(created_at) / 6.0)  # saturate after 6 hours
    score = 0.45*u + 0.25*s + 0.20*gap + 0.10*a
    return round(max(0.0, min(1.0, score)), 3)

def rank_reason_text(urgency: str, severity: int, progress: float, created_at) -> str:
    parts = []
    if urgency == "now": parts.append("time-critical")
    elif urgency == "today": parts.append("needed today")
    if severity >= 4: parts.append("high severity")
    if progress < 0.5: parts.append("large funding gap")
    if age_hours(created_at) >= 2: parts.append("waiting for help")
    if not parts: parts.append("general need")
    return ", ".join(parts[:3])
