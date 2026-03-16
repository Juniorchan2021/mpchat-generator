import asyncio

from fastapi import APIRouter, HTTPException

from api.models.requests import ImageSearchRequest, LinksRequest, SchemaRequest, SerpAnalyzeRequest, SlugRequest
from core.geo_tools import generate_faq_schema
from core.image_client import fetch_images_for_article
from core.seo_tools import generate_internal_links, generate_schema, generate_slug
from core.serp_analyzer import analyze_serp

router = APIRouter(prefix="/api/v1", tags=["tools"])


@router.post("/schema")
async def create_schema(req: SchemaRequest):
    article_schema = generate_schema(
        title=req.title,
        description=req.description,
        author=req.author,
        date=req.date,
        image_url=req.image_url,
        article_url=req.article_url,
    )
    faq_schema = generate_faq_schema(req.faq_pairs)
    return {
        "article_schema": article_schema,
        "faq_schema": faq_schema,
    }


@router.post("/slug")
async def create_slug(req: SlugRequest):
    return {"slug": generate_slug(req.title)}


@router.post("/links")
async def create_links(req: LinksRequest):
    return {"links": generate_internal_links(req.selling_points)}


@router.post("/serp/analyze")
async def serp_analyze(req: SerpAnalyzeRequest):
    try:
        return await asyncio.to_thread(analyze_serp, req.keyword)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"SERP 分析失败: {type(e).__name__}: {e}")


@router.post("/images/search")
async def image_search(req: ImageSearchRequest):
    try:
        images = await asyncio.to_thread(
            fetch_images_for_article,
            pixabay_key=req.pixabay_key,
            pexels_key=req.pexels_key,
            scenario_terms=req.scenario_terms,
            ai_terms=req.ai_terms,
            article_title=req.article_title,
            per_query=req.per_query,
        )
        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"图片搜索失败: {type(e).__name__}: {e}")
