from fastapi import APIRouter
from app.models import AInvokeIn, AInvokeOut
from app.llm import ai_invoke

router = APIRouter()

@router.post("/ai/invoke", response_model=AInvokeOut)
async def invoke(payload: AInvokeIn):
    result = await ai_invoke(payload.text)

    draft = result["draft"]
    # include affordability (frontend needs it)
    draft["requester_afford"] = float(payload.requester_afford)

    return AInvokeOut(
        request_draft=draft,
        confidence=float(result["confidence"])
    )
