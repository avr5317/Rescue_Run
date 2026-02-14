from fastapi import APIRouter
import secrets
from app.models import DeviceOut

router = APIRouter()

@router.post("/device", response_model=DeviceOut)
def create_device():
    return DeviceOut(device_token="dev_" + secrets.token_urlsafe(16))
