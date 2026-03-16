from fastapi import APIRouter

from api.models.requests import AiDetectRequest, OptimizeRequest
from api.models.responses import OptimizeResponse
from api.services import detect_ai_content, optimize_article_content

router = APIRouter(prefix="/api/v1", tags=["optimize"])


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_article(req: OptimizeRequest):
    result = optimize_article_content(
        article=req.article,
        keywords=req.keywords,
        mode=req.mode,
        api_key=req.api_key,
        model=req.model,
        base_url=req.base_url,
        provider=req.provider,
    )
    return OptimizeResponse(**result)


@router.post("/detect/ai")
async def detect_ai(req: AiDetectRequest):
    return {
        "result": detect_ai_content(
            article=req.article,
            api_key=req.api_key,
            model=req.model,
            base_url=req.base_url,
            provider=req.provider,
        )
    }
