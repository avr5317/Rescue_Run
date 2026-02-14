from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.device import router as device_router
from app.routes.requests import router as requests_router
from app.routes.ai_routes import router as ai_router
from app.routes.shop_routing import router as shop_routing_router


app = FastAPI(title="Mutual Aid API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(device_router, prefix="/v1", tags=["device"])
app.include_router(ai_router, prefix="/v1", tags=["ai"])
app.include_router(requests_router, prefix="/v1", tags=["requests"])
app.include_router(shop_routing_router, prefix="/v1", tags=["shops"])

