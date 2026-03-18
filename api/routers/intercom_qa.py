import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import verify_api_key
from api.models.requests import IntercomQARequest, IntercomUploadRequest
from api.models.responses import IntercomCollectionItem, IntercomCollectionsResponse, IntercomQAResponse
from core.intercom_qa import fetch_intercom_collections, generate_qa_pairs, upload_to_intercom

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/intercom", tags=["intercom"], dependencies=[Depends(verify_api_key)])


@router.get("/collections", response_model=IntercomCollectionsResponse)
async def get_intercom_collections(token: str = Query(..., min_length=1)):
    """Fetch all Collections from Intercom Help Center using the provided token."""
    try:
        raw_collections = await asyncio.to_thread(fetch_intercom_collections, token)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("获取 Intercom Collections 失败: %s", e)
        raise HTTPException(status_code=502, detail=f"Intercom API 调用失败: {e}")

    items = [
        IntercomCollectionItem(
            id=c["id"],
            name=c["name"],
            translated_content=c.get("translated_content", {}),
        )
        for c in raw_collections
    ]
    return IntercomCollectionsResponse(collections=items, count=len(items))


@router.post("/generate-qa", response_model=IntercomQAResponse)
async def generate_intercom_qa(req: IntercomQARequest):
    """Generate multilingual Q&A pairs for Intercom Help Center based on a feature description."""
    try:
        qa_by_language = await asyncio.to_thread(
            generate_qa_pairs,
            provider=req.provider,
            api_key=req.api_key,
            base_url=req.base_url,
            model=req.model,
            feature_description=req.feature_description,
            product_name=req.product_name,
            tone=req.tone,
            count=req.count,
            languages=req.languages,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("QA 生成失败: %s", e)
        raise HTTPException(status_code=502, detail=f"LLM 调用失败: {e}")

    count_per_language = {lang: len(pairs) for lang, pairs in qa_by_language.items()}
    return IntercomQAResponse(
        qa_by_language=qa_by_language,
        languages=req.languages,
        count_per_language=count_per_language,
    )


@router.post("/upload")
async def upload_intercom_article(req: IntercomUploadRequest):
    """Upload an article to Intercom Help Center."""
    try:
        result = await asyncio.to_thread(
            upload_to_intercom,
            token=req.intercom_token,
            collection_id=req.collection_id,
            title=req.title,
            body=req.body,
            state=req.state,
            locale=req.locale,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Intercom 上传失败: %s", e)
        raise HTTPException(status_code=502, detail=f"Intercom API 调用失败: {e}")

    return {
        "ok": True,
        "article_id": str(result.get("id", "")),
        "url": result.get("url", ""),
    }
