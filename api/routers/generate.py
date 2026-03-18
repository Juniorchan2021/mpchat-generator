import asyncio
import logging
import os
from functools import partial

from fastapi import APIRouter, HTTPException

from api.models.requests import GenerateRequest
from api.models.responses import GenerateResponse
from api.utils import locate_scenario, selling_points_text, style_to_instruction
from core.generation import generate_article, validate_keywords
from core.image_client import fetch_images_for_article
from core.knowledge import fetch_web_knowledge
from core.seo_tools import generate_slug, reading_stats
from core.serp_analyzer import analyze_serp, serp_to_prompt_context

router = APIRouter(prefix="/api/v1", tags=["generate"])
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=GenerateResponse)
async def create_article(req: GenerateRequest):
    keyword_error = validate_keywords(req.keywords)
    if keyword_error:
        raise HTTPException(status_code=422, detail=keyword_error)

    scenario = locate_scenario(req.category, req.scenario)
    style_instruction = style_to_instruction(req.style)
    selected_points = req.selling_points or scenario.get("selling_points", [])

    web_sources: list[dict] = []
    web_content = ""
    if req.use_web:
        web_content, web_sources = await asyncio.to_thread(fetch_web_knowledge)

    serp_data = None
    if req.use_serp and req.keywords.strip():
        primary_keyword = req.keywords.split(",")[0].strip()
        try:
            serp_data = await asyncio.to_thread(analyze_serp, primary_keyword)
            if serp_data:
                web_content += "\n\n" + serp_to_prompt_context(serp_data)
        except Exception as e:
            logger.warning("SERP analysis failed: %s", e)

    try:
        result = await asyncio.to_thread(
            partial(
                generate_article,
                model=req.model,
                language=req.language,
                scenario_label=req.scenario,
                audience_tag=scenario.get("audience_tag", ""),
                selling_points_text=selling_points_text(selected_points),
                style_name=req.style,
                style_instruction=style_instruction,
                keywords=req.keywords,
                web_content=web_content,
                geo_mode=req.geo_mode,
                word_count_target=req.word_count_target,
                provider=req.provider,
                api_key=req.api_key,
                base_url=req.base_url,
                target_title=req.target_title,
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"文章生成失败: {type(e).__name__}: {e}")

    title = result.get("seo_title", req.scenario)
    article = result.get("article", "")
    stats = await asyncio.to_thread(reading_stats, article, req.keywords)

    images: list[dict] = []
    if req.include_images:
        try:
            fetched = await asyncio.to_thread(
                partial(
                    fetch_images_for_article,
                    pixabay_key=os.getenv("PIXABAY_API_KEY", "46561407-37c6214d0e52dffc32a430eb3"),
                    pexels_key=os.getenv("PEXELS_API_KEY", "YszqWzFI3WsjAq1gxox3BHOTfD3bOLlFmQZBoap418G6YYVaxhWC1HZz"),
                    scenario_terms=scenario.get("pixabay_terms", []),
                    ai_terms=result.get("image_search_terms", []),
                    article_title=title,
                    per_query=max(1, min(req.image_count, 3)),
                )
            )
            images = fetched[: req.image_count]
        except Exception as e:
            logger.warning("Image fetching failed, proceeding without images: %s", e)

    return GenerateResponse(
        title=title,
        meta_description=result.get("meta_description", ""),
        slug=result.get("slug_suggestion") or generate_slug(title),
        ab_titles=result.get("title_alternatives", []),
        article=article,
        faq_pairs=result.get("faq_pairs", []),
        images=images,
        image_prompts=result.get("image_prompts", []),
        image_search_terms=result.get("image_search_terms", []),
        word_count=stats.get("word_count", 0),
        reading_time_min=stats.get("reading_time_min", 0),
        web_sources=web_sources,
        serp=serp_data,
    )
