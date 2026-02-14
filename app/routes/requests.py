from fastapi import APIRouter, Header, HTTPException, Query
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import ReturnDocument

from app.db import requests_col, donations_col
from app.models import CreateRequestIn, RequestDetailOut, DonateIn, DonateOut, RankOut, ClaimOut, StatusUpdateIn
from app.triage import compute_funding_goal, progress_ratio, rank_score, rank_reason_text

from app.progress import progress_fields, utc_time

router = APIRouter()

def require_device(x_device_token: str | None) -> str:
    if not x_device_token:
        raise HTTPException(status_code=400, detail="Missing X-Device-Token")
    return x_device_token

def oid(s: str) -> ObjectId:
    try:
        return ObjectId(s)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid id")

def public_location(loc: dict) -> dict:
    # Optional blur: keep as-is for MVP
    return {"lat": float(loc["lat"]), "lng": float(loc["lng"])}

@router.post("/requests")
def create_request(payload: CreateRequestIn, x_device_token: str | None = Header(default=None, alias="X-Device-Token")):
    device = require_device(x_device_token)

    funding_goal = compute_funding_goal(payload.estimated_total, payload.requester_afford)
    funded_amount = 0.0
    prog = progress_ratio(funded_amount, funding_goal)

    now = datetime.now(timezone.utc)
    rscore = rank_score(payload.urgency_window, payload.severity, prog, now)
    rreason = rank_reason_text(payload.urgency_window, payload.severity, prog, now)

    doc = {
        "created_at": now,
        "updated_at": now,
        "created_by": device,

        "raw_text": payload.raw_text,
        "category": payload.category,
        "urgency_window": payload.urgency_window,
        "severity": payload.severity,
        "items": [it.model_dump() for it in payload.items],

        "location": public_location(payload.location.model_dump()),
        "status": "funded" if funding_goal <= 0 else "open",
        "status_history": [{"status": "open", "at": now}] + (
            [{"status": "funded", "at": now}] if funding_goal <= 0 else []
        ),

        "estimated_total": round(float(payload.estimated_total), 2),
        "requester_afford": round(float(payload.requester_afford), 2),
        "funding_goal": round(float(funding_goal), 2),
        "funded_amount": 0.0,
        "progress": prog,

        "rank_score": rscore,
        "rank_reason": rreason,
        "claim": None,
    }

    res = requests_col.insert_one(doc)
    return {"request": {"id": str(res.inserted_id), **{k: doc[k] for k in [
        "status","funding_goal","funded_amount","progress","rank_score", "created_at", "updated_at", "status_history"
    ]}}}

@router.get("/requests")
def list_requests(
    bbox: str | None = Query(default=None, description="minLat,minLng,maxLat,maxLng"),
    status: str | None = Query(default=None, description="open|funded|claimed|on_the_way|delivered|cancelled"),
    sort: str = Query(default="rank", description="rank|new"),
    limit: int = Query(default=200, ge=1, le=1000),
):
    q = {}
    if status:
        q["status"] = status

    if bbox:
        try:
            minLat, minLng, maxLat, maxLng = [float(x) for x in bbox.split(",")]
        except Exception:
            raise HTTPException(status_code=400, detail="bbox must be minLat,minLng,maxLat,maxLng")
        q["location.lat"] = {"$gte": minLat, "$lte": maxLat}
        q["location.lng"] = {"$gte": minLng, "$lte": maxLng}

    proj = {
        "category": 1, "urgency_window": 1, "severity": 1, "status": 1,
        "location": 1, "estimated_total": 1, "requester_afford": 1,
        "funding_goal": 1, "funded_amount": 1, "progress": 1,
        "rank_score": 1, "created_at": 1, "updated_at": 1
    }

    cursor = requests_col.find(q, proj)
    if sort == "new":
        cursor = cursor.sort("created_at", -1)
    else:
        cursor = cursor.sort("rank_score", -1).sort("created_at", -1)

    cursor = cursor.limit(limit)

    out = []
    for d in cursor:
        out.append({
            "id": str(d["_id"]),
            "category": d["category"],
            "urgency_window": d["urgency_window"],
            "severity": d["severity"],
            "status": d["status"],
            "lat": d["location"]["lat"],
            "lng": d["location"]["lng"],
            "estimated_total": float(d["estimated_total"]),
            "requester_afford": float(d["requester_afford"]),
            "funding_goal": float(d["funding_goal"]),
            "funded_amount": float(d["funded_amount"]),
            "progress": float(d["progress"]),
            "rank_score": float(d.get("rank_score", 0.0)),
            "created_at": utc_time(d.get("created_at")),
            "updated_at": utc_time(d.get("updated_at") or d.get("created_at")),
        })

    return {"requests": out}

@router.get("/requests/{request_id}")
def get_request(request_id: str, x_device_token: str | None = Header(default=None, alias="X-Device-Token")):
    d = requests_col.find_one({"_id": oid(request_id)})
    if not d:
        raise HTTPException(status_code=404, detail="not found")
    return {
        "request": {
            "id": str(d["_id"]),
            "raw_text": d["raw_text"],
            "category": d["category"],
            "urgency_window": d["urgency_window"],
            "severity": d["severity"],
            "status": d["status"],
            "lat": d["location"]["lat"],
            "lng": d["location"]["lng"],
            "items": d.get("items", []),
            "estimated_total": float(d["estimated_total"]),
            "requester_afford": float(d["requester_afford"]),
            "funding_goal": float(d["funding_goal"]),
            "funded_amount": float(d["funded_amount"]),
            "progress": float(d["progress"]),
            "rank_score": float(d.get("rank_score", 0.0)),
            "rank_reason": d.get("rank_reason", ""),
            **progress_fields(d, x_device_token),
        }
    }

@router.post("/requests/{request_id}/donate", response_model=DonateOut)
def donate(
    request_id: str,
    payload: DonateIn,
    x_device_token: str | None = Header(default=None, alias="X-Device-Token"),
):
    donor = require_device(x_device_token)
    rid = oid(request_id)
    amount = round(float(payload.amount), 2)

    if amount <= 0:
        raise HTTPException(status_code=422, detail="Donation must be at least $0.01")

    # Compare-and-set keeps funding updates from resetting a concurrent claim
    # and prevents two donors from overwriting each other's totals.
    for _ in range(5):
        current = requests_col.find_one({"_id": rid})
        if not current:
            raise HTTPException(status_code=404, detail="not found")
        if current["status"] not in ["open", "funded"]:
            raise HTTPException(status_code=409, detail="Request is no longer accepting funding")
        now = datetime.now(timezone.utc)
        funded = round(float(current["funded_amount"]) + amount, 2)
        goal = float(current["funding_goal"])
        prog = progress_ratio(funded, goal)
        status = "funded" if goal <= 0 or funded >= goal else current["status"]
        changes = {"$set": {
            "funded_amount": funded, "progress": prog, "status": status,
            "updated_at": now,
            "rank_score": rank_score(current["urgency_window"], current["severity"], prog, current["created_at"]),
            "rank_reason": rank_reason_text(current["urgency_window"], current["severity"], prog, current["created_at"]),
        }}
        if status != current["status"]:
            changes["$push"] = {"status_history": {"status": status, "at": now}}
        updated = requests_col.find_one_and_update(
            {"_id": rid, "status": current["status"], "funded_amount": current["funded_amount"]},
            changes, return_document=ReturnDocument.AFTER,
        )
        if updated:
            break
    else:
        raise HTTPException(status_code=409, detail="Request changed; refresh and try again")

    donations_col.insert_one({"request_id": rid, "donor_id": donor, "amount": amount, "created_at": now})
    return DonateOut(request={
        "id": request_id,
        **{key: updated[key] for key in ["funded_amount", "funding_goal", "progress", "status", "rank_score", "rank_reason"]},
        **progress_fields(updated, donor),
    })

@router.post("/ai/rank", response_model=RankOut)
def ai_rank():
    # Recompute rank_score for all OPEN requests (or open+funded if you want)
    q = {"status": {"$in": ["open", "funded"]}}
    cursor = requests_col.find(q, {"urgency_window": 1, "severity": 1, "progress": 1, "created_at": 1})
    updated_count = 0
    now = datetime.now(timezone.utc)

    for d in cursor:
        prog = float(d.get("progress", 0.0))
        rscore = rank_score(d["urgency_window"], int(d["severity"]), prog, d["created_at"])
        rreason = rank_reason_text(d["urgency_window"], int(d["severity"]), prog, d["created_at"])
        requests_col.update_one({"_id": d["_id"]}, {"$set": {"rank_score": rscore, "rank_reason": rreason, "ranked_at": now}})
        updated_count += 1

    return RankOut(updated=updated_count)

@router.post("/requests/{request_id}/claim", response_model=ClaimOut)
def claim(
    request_id: str,
    x_device_token: str | None = Header(default=None, alias="X-Device-Token"),
):
    helper = require_device(x_device_token)
    rid = oid(request_id)

    now = datetime.now(timezone.utc)
    updated = requests_col.find_one_and_update(
        {"_id": rid, "status": "funded", "claim": None},
        {"$set": {
            "status": "claimed",
            "claim": {"helper_id": helper, "claimed_at": now},
            "updated_at": now,
        }, "$push": {"status_history": {"status": "claimed", "at": now}}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        current = requests_col.find_one({"_id": rid})
        if not current:
            raise HTTPException(status_code=404, detail="not found")
        # Retrying the same helper's claim should not add a duplicate event.
        if (current.get("claim") or {}).get("helper_id") == helper:
            updated = current
        else:
            raise HTTPException(status_code=409, detail="Request is no longer available to claim")
    return ClaimOut(request={"id": request_id, "status": updated["status"], **progress_fields(updated, helper)})


def advance_delivery(request_id, target, helper):
    rid = oid(request_id)
    current = requests_col.find_one({"_id": rid})
    if not current:
        raise HTTPException(status_code=404, detail="not found")
    if (current.get("claim") or {}).get("helper_id") != helper:
        raise HTTPException(status_code=403, detail="Only the assigned helper can update delivery progress")
    if current["status"] == target:
        return {"request": {"id": request_id, "status": target, **progress_fields(current, helper)}}
    expected = {"on_the_way": "claimed", "delivered": "on_the_way"}[target]
    if current["status"] != expected:
        raise HTTPException(status_code=409, detail=f"Cannot change {current['status']} to {target}; refresh the request")
    now = datetime.now(timezone.utc)
    updated = requests_col.find_one_and_update(
        {"_id": rid, "status": expected, "claim.helper_id": helper},
        {"$set": {"status": target, "updated_at": now},
         "$push": {"status_history": {"status": target, "at": now}}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        # Handle a concurrent retry of this exact transition idempotently.
        current = requests_col.find_one({"_id": rid})
        if current and current["status"] == target and (current.get("claim") or {}).get("helper_id") == helper:
            updated = current
        else:
            raise HTTPException(status_code=409, detail="Request changed; refresh and try again")
    return {"request": {"id": request_id, "status": target, **progress_fields(updated, helper)}}


@router.patch("/requests/{request_id}/status")
def update_status(
    request_id: str,
    payload: StatusUpdateIn,
    x_device_token: str | None = Header(default=None, alias="X-Device-Token"),
):
    return advance_delivery(request_id, payload.status, require_device(x_device_token))


@router.post("/requests/{request_id}/delivered")
def delivered(
    request_id: str,
    x_device_token: str | None = Header(default=None, alias="X-Device-Token"),
):
    # Preserve the endpoint, with the same transition rules as PATCH /status.
    return advance_delivery(request_id, "delivered", require_device(x_device_token))
