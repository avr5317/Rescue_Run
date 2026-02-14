from pydantic import BaseModel, Field, conlist
from typing import Literal, List, Optional, Dict, Any
from datetime import datetime

Category = Literal["meds", "groceries", "shelter", "transport", "other"]
Urgency = Literal["now", "today", "week"]
Status = Literal["open", "funded", "claimed", "on_the_way", "delivered", "cancelled"]

class StatusUpdateIn(BaseModel):
    status: Literal["on_the_way", "delivered"]

class StatusEvent(BaseModel):
    status: Status
    at: Optional[datetime] = None

class LatLng(BaseModel):
    lat: float
    lng: float

class NearestShop(BaseModel):
    shop: str
    price: float
    address: str
    lat: float
    lng: float
    distance_km: float
    distance_mi: float
    navigation_link: str

class ShopPrice(BaseModel):
    shop: str
    price: float
    link: str = ""

class Item(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    qty: float = Field(default=1, ge=0.0)
    unit: str = Field(default="unit", max_length=30)
    notes: str = Field(default="", max_length=120)
    shops: List[str] = Field(default_factory=list)  # Shop names from SerpAPI (for backward compatibility)
    shop_prices: List[ShopPrice] = Field(default_factory=list)  # Detailed price info from SerpAPI



class AInvokeIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    location: LatLng
    requester_afford: float = Field(ge=0.0, le=10000.0)

class AInvokeOut(BaseModel):
    request_draft: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)

class CreateRequestIn(BaseModel):
    raw_text: str = Field(min_length=1, max_length=500)
    category: Category
    urgency_window: Urgency
    severity: int = Field(ge=1, le=5)
    items: List[Item] = []
    estimated_total: float = Field(ge=0.0, le=2000.0)
    requester_afford: float = Field(ge=0.0, le=2000.0)
    location: LatLng

class RequestCardOut(BaseModel):
    id: str
    category: Category
    urgency_window: Urgency
    severity: int
    status: Status
    lat: float
    lng: float
    estimated_total: float
    requester_afford: float
    funding_goal: float
    funded_amount: float
    progress: float
    rank_score: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RequestDetailOut(RequestCardOut):
    raw_text: str
    items: List[Item]
    rank_reason: str
    created_at: datetime
    updated_at: datetime
    claim: Optional[Dict[str, Any]] = None
    status_history: List[StatusEvent] = Field(default_factory=list)
    is_claiming_helper: bool = False

class DonateIn(BaseModel):
    amount: float = Field(gt=0.0, le=2000.0)

class DonateOut(BaseModel):
    request: Dict[str, Any]

class ClaimOut(BaseModel):
    request: Dict[str, Any]

class DeviceOut(BaseModel):
    device_token: str

class RankOut(BaseModel):
    updated: int
