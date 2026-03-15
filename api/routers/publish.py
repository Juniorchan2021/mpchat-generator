from fastapi import APIRouter, Depends

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
)

router = APIRouter(prefix="/api/v1/publish", tags=["publish"], dependencies=[Depends(verify_api_key)])


@router.post("/devto")
async def publish_devto(req: PublishRequest):
    return publish_to_devto(
        api_key=req.api_key,
        title=req.title,
        body_markdown=req.article,
        tags=req.tags,
        canonical_url=req.canonical_url,
        published=req.published,
    )


@router.post("/hashnode")
async def publish_hashnode(req: PublishRequest):
    return publish_to_hashnode(
        token=req.token,
        publication_id=req.publication_id,
        title=req.title,
        body_markdown=req.article,
        tags=req.tags,
        slug=req.slug,
    )


@router.post("/medium")
async def preview_medium(req: PublishRequest):
    return {"ok": True, "preview": format_for_medium(req.title, req.article, req.meta_description, req.canonical_url)}


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
