from fastapi import APIRouter, Depends, HTTPException

from api.deps import verify_api_key
from core.providers import list_providers
from core.scenarios import ARTICLE_STYLES, KEYWORD_PRESETS, LANGUAGES, SCENARIO_CATEGORIES, SELLING_POINT_GROUPS

router = APIRouter(prefix="/api/v1/config", tags=["config"], dependencies=[Depends(verify_api_key)])


@router.get("/providers")
async def get_providers():
    try:
        return list_providers()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取 providers 失败: {type(e).__name__}: {e}")


@router.get("/scenarios")
async def get_scenarios():
    try:
        return {
            "scenario_categories": SCENARIO_CATEGORIES,
            "article_styles": ARTICLE_STYLES,
            "keyword_presets": KEYWORD_PRESETS,
            "languages": LANGUAGES,
            "selling_point_groups": SELLING_POINT_GROUPS,
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取 scenarios 失败: {type(e).__name__}: {e}")


@router.get("/all")
async def get_all_config():
    try:
        return {
            "providers": list_providers(),
            "scenario_categories": SCENARIO_CATEGORIES,
            "article_styles": ARTICLE_STYLES,
            "keyword_presets": KEYWORD_PRESETS,
            "languages": LANGUAGES,
            "selling_point_groups": SELLING_POINT_GROUPS,
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取全量配置失败: {type(e).__name__}: {e}")
