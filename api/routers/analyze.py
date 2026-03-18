from fastapi import APIRouter, Depends, HTTPException

from api.deps import verify_api_key
from api.models.requests import ArticleAnalyzeRequest
from api.models.responses import AnalyzeResponse
from core.geo_tools import geo_score
from core.seo_tools import reading_stats

router = APIRouter(prefix="/api/v1/analyze", tags=["analyze"], dependencies=[Depends(verify_api_key)])


@router.post("/seo", response_model=AnalyzeResponse)
async def analyze_seo(req: ArticleAnalyzeRequest):
    try:
        stats = reading_stats(req.article, req.keywords)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"SEO 分析失败: {type(e).__name__}: {e}")
    suggestions: list[str] = []
    if stats.get("h1_count", 0) < 1:
        suggestions.append("补充 1 个 H1 标题。")
    if stats.get("h2_count", 0) < 2:
        suggestions.append("至少补充 2-3 个 H2 结构段落。")
    if not stats.get("has_cta"):
        suggestions.append("在结尾增加 CTA，引导访问 mp.net。")
    if req.keywords and not stats.get("keyword_density"):
        suggestions.append("补充目标关键词并控制在自然密度范围内。")

    return AnalyzeResponse(
        score=stats.get("structure_score", 0),
        breakdown={
            "word_count": stats.get("word_count", 0),
            "reading_time_min": stats.get("reading_time_min", 0),
            "h1_count": stats.get("h1_count", 0),
            "h2_count": stats.get("h2_count", 0),
            "has_cta": stats.get("has_cta", False),
            "keyword_density": stats.get("keyword_density", {}),
        },
        suggestions=suggestions,
        details=stats,
    )


@router.post("/geo", response_model=AnalyzeResponse)
async def analyze_geo(req: ArticleAnalyzeRequest):
    try:
        result = geo_score(req.article, req.faq_pairs)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GEO 分析失败: {type(e).__name__}: {e}")
    return AnalyzeResponse(
        score=result.get("score", 0),
        breakdown=result.get("details", {}),
        suggestions=result.get("tips", []),
        details=result,
    )
