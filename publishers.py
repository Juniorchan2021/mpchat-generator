"""
MPChat v4.0 — Multi-platform content distribution
API direct-publish: Dev.to, Hashnode
Format-and-copy: Medium, LinkedIn, Twitter thread, Zhihu, WeChat, Crypto blogs
"""

import json
import re
import textwrap
import requests


# ══════════════════════════════════════════════════════════════════════════════
# API Direct Publishing
# ══════════════════════════════════════════════════════════════════════════════

def publish_to_devto(
    api_key: str,
    title: str,
    body_markdown: str,
    tags: list[str] | None = None,
    canonical_url: str = "",
    published: bool = False,
) -> dict:
    """Publish article to Dev.to via API."""
    if not api_key or not api_key.strip():
        return {"ok": False, "error": "Dev.to API Key 未配置"}
    headers = {
        "api-key": api_key.strip(),
        "Content-Type": "application/json",
    }
    payload = {
        "article": {
            "title": title,
            "body_markdown": body_markdown,
            "published": published,
            "tags": (tags or [])[:4],
        }
    }
    if canonical_url:
        payload["article"]["canonical_url"] = canonical_url
    try:
        r = requests.post(
            "https://dev.to/api/articles",
            headers=headers,
            json=payload,
            timeout=30,
        )
        if r.status_code in (200, 201):
            data = r.json()
            return {"ok": True, "url": data.get("url", ""), "id": data.get("id")}
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def publish_to_hashnode(
    token: str,
    publication_id: str,
    title: str,
    body_markdown: str,
    tags: list[str] | None = None,
    slug: str = "",
) -> dict:
    """Publish article to Hashnode via GraphQL API."""
    if not token or not publication_id:
        return {"ok": False, "error": "Hashnode Token 或 Publication ID 未配置"}
    query = """
    mutation PublishPost($input: PublishPostInput!) {
        publishPost(input: $input) {
            post {
                id
                url
                slug
            }
        }
    }
    """
    tag_objects = [{"name": t, "slug": t.lower().replace(" ", "-")} for t in (tags or [])[:5]]
    variables = {
        "input": {
            "title": title,
            "contentMarkdown": body_markdown,
            "publicationId": publication_id,
            "tags": tag_objects,
        }
    }
    if slug:
        variables["input"]["slug"] = slug
    try:
        r = requests.post(
            "https://gql.hashnode.com",
            headers={
                "Authorization": token.strip(),
                "Content-Type": "application/json",
            },
            json={"query": query, "variables": variables},
            timeout=30,
        )
        if r.status_code not in (200, 201):
            return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
        data = r.json()
        post = (data.get("data") or {}).get("publishPost", {}).get("post")
        if post:
            return {"ok": True, "url": post.get("url", ""), "id": post.get("id")}
        errors = data.get("errors", [])
        err_msg = errors[0].get("message", "Unknown error") if errors else "No post returned"
        return {"ok": False, "error": err_msg}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# Format Converters (copy-ready)
# ══════════════════════════════════════════════════════════════════════════════

def publish_to_paragraph(
    api_key: str,
    title: str,
    body_markdown: str,
    tags: list[str] | None = None,
    canonical_url: str = "",
) -> dict:
    """Publish article to Paragraph.xyz via API."""
    if not api_key or not api_key.strip():
        return {"ok": False, "error": "Paragraph API Key 未配置"}
    if not title or not title.strip():
        return {"ok": False, "error": "标题不能为空"}
    if not body_markdown or not body_markdown.strip():
        return {"ok": False, "error": "文章内容不能为空"}

    headers = {
        "Authorization": api_key.strip(),
        "Content-Type": "application/json",
    }
    payload: dict = {
        "title": title,
        "bodyMarkdown": body_markdown,
        "tags": (tags or [])[:5],
    }
    if canonical_url:
        payload["canonicalUrl"] = canonical_url

    try:
        r = requests.post(
            "https://api.paragraph.xyz/blogs/posts",
            headers=headers,
            json=payload,
            timeout=30,
        )
        if r.status_code in (200, 201):
            data = r.json()
            return {"ok": True, "url": data.get("url", ""), "id": data.get("id")}
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def publish_to_medium(
    token: str,
    title: str,
    body_markdown: str,
    tags: list[str] | None = None,
    canonical_url: str = "",
    publish_status: str = "draft",
) -> dict:
    """Publish article to Medium via API. Falls back to format preview if token is missing or /me fails."""
    if not token or not token.strip():
        return {"ok": True, "preview": format_for_medium(title, body_markdown, "", canonical_url)}

    auth_headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Charset": "utf-8",
    }

    # Step 1: fetch authenticated user id
    try:
        me_resp = requests.get(
            "https://api.medium.com/v1/me",
            headers=auth_headers,
            timeout=15,
        )
        if me_resp.status_code != 200:
            return {"ok": True, "preview": format_for_medium(title, body_markdown, "", canonical_url)}
        user_id = me_resp.json().get("data", {}).get("id", "")
    except Exception:
        return {"ok": True, "preview": format_for_medium(title, body_markdown, "", canonical_url)}

    if not user_id:
        return {"ok": True, "preview": format_for_medium(title, body_markdown, "", canonical_url)}

    # Step 2: create post
    payload: dict = {
        "title": title,
        "contentFormat": "markdown",
        "content": body_markdown,
        "tags": (tags or [])[:5],
        "publishStatus": publish_status if publish_status in ("draft", "public", "unlisted") else "draft",
    }
    if canonical_url:
        payload["canonicalUrl"] = canonical_url

    try:
        post_resp = requests.post(
            f"https://api.medium.com/v1/users/{user_id}/posts",
            headers=auth_headers,
            json=payload,
            timeout=30,
        )
        if post_resp.status_code in (200, 201):
            data = post_resp.json().get("data", {})
            return {"ok": True, "url": data.get("url", ""), "id": data.get("id")}
        return {"ok": False, "error": f"HTTP {post_resp.status_code}: {post_resp.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def format_for_medium(
    title: str, article: str, meta_desc: str = "", canonical_url: str = ""
) -> str:
    """Format article for Medium (Markdown import compatible)."""
    header = f"# {title}\n\n"
    if meta_desc:
        header += f"> {meta_desc}\n\n"
    footer = ""
    if canonical_url:
        footer = f"\n\n---\n*Originally published at [{canonical_url}]({canonical_url})*"
    return header + article + footer


def format_for_linkedin(
    title: str, article: str, max_chars: int = 3000
) -> str:
    """Format article for LinkedIn post (plain text, concise)."""
    clean = re.sub(r"#{1,6}\s+", "", article)
    clean = re.sub(r"\*\*(.+?)\*\*", r"\1", clean)
    clean = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", clean)
    clean = re.sub(r"!\[.*?\]\(.*?\)", "", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean)

    post = f"{title}\n\n{clean.strip()}"
    if len(post) > max_chars:
        post = post[: max_chars - 50].rsplit("\n", 1)[0]
        post += "\n\n... [Read full article for more details]"

    post += "\n\n#MPChat #CryptoPayment #Web3 #Fintech #Blockchain"
    return post


def format_for_twitter_thread(
    title: str, article: str, max_tweets: int = 10
) -> list[str]:
    """Split article into a Twitter thread (each tweet <= 280 chars)."""
    clean = re.sub(r"!\[.*?\]\(.*?\)\n?", "", article)
    clean = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 \2", clean)

    sections: list[str] = []
    current = ""
    for line in clean.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            if current.strip():
                sections.append(current.strip())
            current = stripped.replace("## ", "") + "\n\n"
        elif stripped.startswith("# "):
            continue
        else:
            current += stripped + " "
    if current.strip():
        sections.append(current.strip())

    tweets: list[str] = []
    tweets.append(f"{title}\n\nA thread below")

    for section in sections:
        if len(section) <= 270:
            tweets.append(section)
        else:
            words = section.split()
            chunk = ""
            for word in words:
                if len(chunk) + len(word) + 1 > 260:
                    tweets.append(chunk.strip())
                    chunk = word + " "
                else:
                    chunk += word + " "
            if chunk.strip():
                tweets.append(chunk.strip())

    tweets = tweets[:max_tweets]
    result = []
    for i, tweet in enumerate(tweets):
        numbered = f"{i + 1}/{len(tweets)} {tweet}"
        result.append(numbered[:280])
    return result


def format_for_zhihu(title: str, article: str) -> str:
    """Format article for Zhihu (keep Markdown, add attribution)."""
    header = f"# {title}\n\n"
    footer = "\n\n---\n\n> 本文由 MPChat 内容团队出品。了解更多：[mp.net](https://mp.net)"
    return header + article + footer


def format_for_wechat(title: str, article: str) -> str:
    """Format for WeChat Official Account (plain text, no external links)."""
    clean = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", article)
    clean = re.sub(r"!\[.*?\]\(.*?\)\n?", "", clean)
    clean = re.sub(r"#{1,6}\s+(.+)", r"\n【\1】\n", clean)
    clean = re.sub(r"\*\*(.+?)\*\*", r"「\1」", clean)

    header = f"「{title}」\n\n"
    footer = "\n\n——————\n了解更多，搜索 MPChat 或访问 mp.net"
    return header + clean.strip() + footer


def format_for_crypto_submission(
    title: str,
    article: str,
    meta_desc: str = "",
    author: str = "MPChat Team",
    slug: str = "",
) -> str:
    """
    Generate a submission-ready markdown file for crypto blog guest posts
    (CoinTelegraph, Bitcoin Magazine, Decrypt, CryptoSlate, etc.)
    """
    frontmatter = f"""---
title: "{title}"
author: "{author}"
description: "{meta_desc}"
slug: "{slug}"
tags: [crypto, payment, web3, fintech, MPChat]
---

"""
    return frontmatter + article
