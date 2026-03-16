from fastapi import APIRouter

from core.providers import list_providers
from core.scenarios import ARTICLE_STYLES, KEYWORD_PRESETS, LANGUAGES, SCENARIO_CATEGORIES, SELLING_POINT_GROUPS

router = APIRouter(prefix="/api/v1/config", tags=["config"])


@router.get("/providers")
async def get_providers():
    return list_providers()


@router.get("/scenarios")
async def get_scenarios():
    return {
        "scenario_categories": SCENARIO_CATEGORIES,
        "article_styles": ARTICLE_STYLES,
        "keyword_presets": KEYWORD_PRESETS,
        "languages": LANGUAGES,
        "selling_point_groups": SELLING_POINT_GROUPS,
    }


@router.get("/all")
async def get_all_config():
    return {
        "providers": list_providers(),
        "scenario_categories": SCENARIO_CATEGORIES,
        "article_styles": ARTICLE_STYLES,
        "keyword_presets": KEYWORD_PRESETS,
        "languages": LANGUAGES,
        "selling_point_groups": SELLING_POINT_GROUPS,
    }
