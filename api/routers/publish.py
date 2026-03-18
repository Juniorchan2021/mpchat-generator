import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.deps import verify_api_key
from api.models.requests import PublishRequest
from core.publishers import (
    format_for_crypto_submission,
    format_for_linkedin,
    format_for_medium,
    format_for_twitter_thread,
    format_for_wechat,
    format_for_zhihu,
    publish_to_devto,
    publish_to_hashnode,
    publish_to_medium,
    publish_to_paragraph,
)

router = APIRouter(prefix="/api/v1/publish", tags=["publish"], dependencies=[Depends(verify_api_key)])
logger = logging.getLogger(__name__)


@router.post("/devto")
async def publish_devto(req: PublishRequest):
    try:
        return await asyncio.to_thread(
            publish_to_devto,
            api_key=req.api_key,
            title=req.title,
            body_markdown=req.article,
            tags=req.tags,
            canonical_url=req.canonical_url,
            published=req.published,
        )
    except Exception as e:
        logger.error("Dev.to 发布失败: %s", e)
        raise HTTPException(status_code=502, detail=f"Dev.to 发布失败: {type(e).__name__}: {e}")


@router.post("/hashnode")
async def publish_hashnode(req: PublishRequest):
    try:
        return await asyncio.to_thread(
            publish_to_hashnode,
            token=req.token,
            publication_id=req.publication_id,
            title=req.title,
            body_markdown=req.article,
            tags=req.tags,
            slug=req.slug,
        )
    except Exception as e:
        logger.error("Hashnode 发布失败: %s", e)
        raise HTTPException(status_code=502, detail=f"Hashnode 发布失败: {type(e).__name__}: {e}")


@router.post("/medium")
async def publish_medium(req: PublishRequest):
    """Publish to Medium via API if medium_token provided; fallback to format preview."""
    if req.medium_token:
        try:
            publish_status = "draft" if req.published is False else "public"
            return await asyncio.to_thread(
                publish_to_medium,
                token=req.medium_token,
                title=req.title,
                body_markdown=req.article,
                tags=req.tags,
                canonical_url=req.canonical_url,
                publish_status=publish_status,
            )
        except Exception as e:
            logger.error("Medium 发布失败: %s", e)
            raise HTTPException(status_code=502, detail=f"Medium 发布失败: {type(e).__name__}: {e}")
    return {"ok": True, "preview": format_for_medium(req.title, req.article, req.meta_description, req.canonical_url)}


@router.post("/paragraph")
async def publish_paragraph(req: PublishRequest):
    """Publish to Paragraph.xyz via API."""
    try:
        return await asyncio.to_thread(
            publish_to_paragraph,
            api_key=req.paragraph_key,
            title=req.title,
            body_markdown=req.article,
            tags=req.tags,
            canonical_url=req.canonical_url,
        )
    except Exception as e:
        logger.error("Paragraph 发布失败: %s", e)
        raise HTTPException(status_code=502, detail=f"Paragraph 发布失败: {type(e).__name__}: {e}")


@router.post("/linkedin")
async def preview_linkedin(req: PublishRequest):
    return {"ok": True, "preview": format_for_linkedin(req.title, req.article)}


@router.post("/twitter")
async def preview_twitter(req: PublishRequest):
    return {"ok": True, "preview": "\n\n---\n\n".join(format_for_twitter_thread(req.title, req.article))}


@router.post("/zhihu")
async def preview_zhihu(req: PublishRequest):
    return {"ok": True, "preview": format_for_zhihu(req.title, req.article)}


@router.post("/wechat")
async def preview_wechat(req: PublishRequest):
    return {"ok": True, "preview": format_for_wechat(req.title, req.article)}


@router.post("/crypto")
async def preview_crypto(req: PublishRequest):
    return {
        "ok": True,
        "preview": format_for_crypto_submission(
            req.title,
            req.article,
            meta_desc=req.meta_description,
            slug=req.slug,
        ),
    }
