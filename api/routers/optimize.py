import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.deps import verify_api_key
from api.models.requests import AiDetectRequest, OptimizeRequest
from api.models.responses import OptimizeResponse
from api.services import detect_ai_content, optimize_article_content

router = APIRouter(prefix="/api/v1", tags=["optimize"], dependencies=[Depends(verify_api_key)])
logger = logging.getLogger(__name__)


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_article(req: OptimizeRequest):
    try:
        result = await asyncio.to_thread(
            optimize_article_content,
            article=req.article,
            keywords=req.keywords,
            mode=req.mode,
            api_key=req.api_key,
            model=req.model,
            base_url=req.base_url,
            provider=req.provider,
        )
    except Exception as e:
        logger.error("文章优化失败: %s", e)
        raise HTTPException(status_code=502, detail=f"优化失败: {type(e).__name__}: {e}")
    return OptimizeResponse(**result)


@router.post("/detect/ai")
async def detect_ai(req: AiDetectRequest):
    try:
        result = await asyncio.to_thread(
            detect_ai_content,
            article=req.article,
            api_key=req.api_key,
            model=req.model,
            base_url=req.base_url,
            provider=req.provider,
        )
    except Exception as e:
        logger.error("AI 检测失败: %s", e)
        raise HTTPException(status_code=502, detail=f"AI 检测失败: {type(e).__name__}: {e}")
    return {"result": result}
