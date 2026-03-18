import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.deps import verify_api_key
from api.models.requests import ExternalAnalyzeRequest, OptimizeRequest, TranslateRequest
from api.models.responses import TranslateResponse
from api.services import optimize_article_content
from core.geo_tools import geo_score
from core.seo_tools import reading_stats
from core.translate import translate_article

router = APIRouter(prefix="/api/v1/external", tags=["external"], dependencies=[Depends(verify_api_key)])
logger = logging.getLogger(__name__)


@router.post("/analyze")
async def analyze_external(req: ExternalAnalyzeRequest):
    try:
        seo = await asyncio.to_thread(reading_stats, req.article, req.keywords)
        geo = await asyncio.to_thread(geo_score, req.article, [])
    except Exception as e:
        logger.error("外部文章分析失败: %s", e)
        raise HTTPException(status_code=502, detail=f"分析失败: {type(e).__name__}: {e}")
    return {
        "seo": seo,
        "geo": geo,
    }


@router.post("/optimize")
async def optimize_external(req: OptimizeRequest):
    try:
        return await asyncio.to_thread(
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
        logger.error("外部文章优化失败: %s", e)
        raise HTTPException(status_code=502, detail=f"优化失败: {type(e).__name__}: {e}")


@router.post("/translate", response_model=TranslateResponse)
async def translate_external(req: TranslateRequest):
    try:
        result = await asyncio.to_thread(
            translate_article,
            provider=req.provider,
            api_key=req.api_key,
            base_url=req.base_url,
            model=req.model,
            article=req.article,
            source_lang=req.source_lang,
            target_lang=req.target_lang,
        )
    except Exception as e:
        logger.error("外部文章翻译失败: %s", e)
        raise HTTPException(status_code=502, detail=f"翻译失败: {type(e).__name__}: {e}")

    return TranslateResponse(
        translated_article=result,
        source_lang=req.source_lang,
        target_lang=req.target_lang,
    )
