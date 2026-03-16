import os

from fastapi import APIRouter, Depends, HTTPException

from api.deps import verify_api_key
from api.models.requests import GenerateRequest
from api.models.responses import GenerateResponse
from api.utils import locate_scenario, selling_points_text, style_to_instruction
from core.generation import generate_article, validate_keywords
from core.image_client import fetch_images_for_article
from core.knowledge import fetch_web_knowledge
from core.seo_tools import generate_slug, reading_stats
from core.serp_analyzer import analyze_serp, serp_to_prompt_context

router = APIRouter(prefix="/api/v1", tags=["generate"], dependencies=[Depends(verify_api_key)])


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
        web_content, web_sources = fetch_web_knowledge()

    serp_data = None
    if req.use_serp and req.keywords.strip():
        primary_keyword = req.keywords.split(",")[0].strip()
        serp_data = analyze_serp(primary_keyword)
        web_content += "\n\n" + serp_to_prompt_context(serp_data)

    result = generate_article(
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
    )

    title = result.get("seo_title", req.scenario)
    article = result.get("article", "")
    stats = reading_stats(article, req.keywords)

    images: list[dict] = []
    if req.include_images:
        images = fetch_images_for_article(
            pixabay_key=os.getenv("PIXABAY_API_KEY", ""),
            pexels_key=os.getenv("PEXELS_API_KEY", ""),
            scenario_terms=scenario.get("pixabay_terms", []),
            ai_terms=result.get("image_search_terms", []),
            article_title=title,
            per_query=max(1, min(req.image_count, 3)),
        )[: req.image_count]

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
