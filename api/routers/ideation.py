import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.deps import verify_api_key
from api.models.requests import IdeationRequest
from api.models.responses import IdeationResponse, TopicSuggestion
from core.ideation import generate_topics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ideation", tags=["ideation"], dependencies=[Depends(verify_api_key)])


@router.post("/topics", response_model=IdeationResponse)
async def get_ideation_topics(req: IdeationRequest):
    """Generate SEO topic suggestions based on a core keyword."""
    try:
        topics_raw = await asyncio.to_thread(
            generate_topics,
            provider=req.provider,
            api_key=req.api_key,
            base_url=req.base_url,
            model=req.model,
            core_keyword=req.core_keyword,
            industry=req.industry,
            count=req.count,
            language=req.language,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("选题生成失败: %s", e)
        raise HTTPException(status_code=502, detail=f"LLM 调用失败: {e}")

    topics = [TopicSuggestion(**t) for t in topics_raw]
    return IdeationResponse(
        topics=topics,
        core_keyword=req.core_keyword,
        count=len(topics),
    )
