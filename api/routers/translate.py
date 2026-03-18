import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.deps import verify_api_key
from api.models.requests import TranslateRequest
from api.models.responses import TranslateResponse
from core.translate import translate_article

router = APIRouter(prefix="/api/v1", tags=["translate"], dependencies=[Depends(verify_api_key)])
logger = logging.getLogger(__name__)


@router.post("/translate", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
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
        logger.error("翻译失败: %s", e)
        raise HTTPException(status_code=502, detail=f"翻译失败: {type(e).__name__}: {e}")

    return TranslateResponse(
        translated_article=result,
        source_lang=req.source_lang,
        target_lang=req.target_lang,
    )
