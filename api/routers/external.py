import asyncio

from fastapi import APIRouter

from api.models.requests import ExternalAnalyzeRequest, OptimizeRequest
from api.services import optimize_article_content
from core.geo_tools import geo_score
from core.seo_tools import reading_stats

router = APIRouter(prefix="/api/v1/external", tags=["external"])


@router.post("/analyze")
async def analyze_external(req: ExternalAnalyzeRequest):
    seo = await asyncio.to_thread(reading_stats, req.article, req.keywords)
    geo = await asyncio.to_thread(geo_score, req.article, [])
    return {
        "seo": seo,
        "geo": geo,
    }


@router.post("/optimize")
async def optimize_external(req: OptimizeRequest):
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
