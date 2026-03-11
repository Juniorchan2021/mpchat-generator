"""
MPChat v4.0.1 — Multi-source image client
Tier 1: Pixabay (primary, proven, API search with metadata)
Tier 2: Pexels (secondary, free 200 req/hr, proper search API)
Tier 3: Placewise CDN (URL-based fallback for article body images, no API key)
"""

import requests

PIXABAY_API_URL = "https://pixabay.com/api/"
PEXELS_API_URL = "https://api.pexels.com/v1/search"
PLACEWISE_CDN = "https://img.placewise.io"


# ── Tier 1: Pixabay (primary) ───────────────────────────────────────────────

def search_pixabay(
    api_key: str,
    query: str,
    count: int = 4,
    orientation: str = "horizontal",
    min_width: int = 800,
) -> list[dict]:
    if not api_key or not api_key.strip() or not query:
        return []
    params = {
        "key": api_key.strip(),
        "q": query[:100],
        "lang": "en",
        "image_type": "photo",
        "orientation": orientation,
        "min_width": min_width,
        "per_page": min(count, 20),
        "safesearch": "true",
    }
    try:
        r = requests.get(PIXABAY_API_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    results = []
    for hit in data.get("hits", [])[:count]:
        results.append({
            "url": hit.get("largeImageURL") or hit.get("webformatURL", ""),
            "preview_url": hit.get("webformatURL", ""),
            "alt_text": query,
            "photographer": hit.get("user", "Unknown"),
            "page_url": hit.get("pageURL", ""),
            "source": "Pixabay",
        })
    return [r for r in results if r["url"]]


# ── Tier 2: Pexels (secondary) ──────────────────────────────────────────────

def search_pexels(
    api_key: str,
    query: str,
    count: int = 4,
    orientation: str = "landscape",
) -> list[dict]:
    if not api_key or not api_key.strip() or not query:
        return []
    headers = {"Authorization": api_key.strip()}
    params = {
        "query": query[:100],
        "per_page": min(count, 15),
        "orientation": orientation,
    }
    try:
        r = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    results = []
    for photo in data.get("photos", [])[:count]:
        src = photo.get("src", {})
        results.append({
            "url": src.get("large") or src.get("original", ""),
            "preview_url": src.get("medium", ""),
            "alt_text": photo.get("alt") or query,
            "photographer": photo.get("photographer", "Unknown"),
            "page_url": photo.get("url", ""),
            "source": "Pexels",
        })
    return [r for r in results if r["url"]]


# ── Tier 3: Placewise CDN (URL-based, no API key) ───────────────────────────

def build_placewise_url(query: str, width: int = 800, height: int = 500) -> str:
    """Build a Placewise CDN image URL from a semantic query."""
    slug = query.strip().lower().replace(" ", "-")[:80]
    return f"{PLACEWISE_CDN}/{width}x{height}-{slug}"


def build_placewise_images(queries: list[str], count: int = 4) -> list[dict]:
    """Generate Placewise CDN image dicts for article body insertion."""
    results = []
    for q in queries[:count]:
        url = build_placewise_url(q)
        results.append({
            "url": url,
            "preview_url": url,
            "alt_text": q,
            "photographer": "Placewise CDN",
            "page_url": "https://placewise.io",
            "source": "Placewise",
            "query": q,
        })
    return results


# ── Unified search ──────────────────────────────────────────────────────────

def build_search_queries(
    scenario_terms: list[str] | None = None,
    ai_terms: list[str] | None = None,
) -> list[str]:
    queries: list[str] = []
    seen = set()
    for src in (scenario_terms or [], ai_terms or []):
        for term in src:
            key = term.strip().lower()
            if key and key not in seen:
                seen.add(key)
                queries.append(term.strip())
    return queries[:5]


def fetch_images_for_article(
    pixabay_key: str = "",
    pexels_key: str = "",
    scenario_terms: list[str] | None = None,
    ai_terms: list[str] | None = None,
    per_query: int = 2,
) -> list[dict]:
    """
    High-level image fetcher with 3-tier fallback:
    1. Pixabay (primary) — needs API key
    2. Pexels (secondary) — needs API key
    3. Placewise CDN (fallback) — no API key, URL-based
    """
    queries = build_search_queries(scenario_terms, ai_terms)
    if not queries:
        return []

    all_images: list[dict] = []

    # Tier 1: Pixabay
    if pixabay_key:
        for q in queries:
            imgs = search_pixabay(pixabay_key, q, count=per_query)
            for img in imgs:
                img["query"] = q
            all_images.extend(imgs)

    # Tier 2: Pexels (fill remaining slots)
    if len(all_images) < 4 and pexels_key:
        remaining = max(1, per_query - (len(all_images) // max(len(queries), 1)))
        for q in queries:
            imgs = search_pexels(pexels_key, q, count=remaining)
            for img in imgs:
                img["query"] = q
            all_images.extend(imgs)

    # Tier 3: Placewise CDN (if both APIs failed)
    if not all_images:
        all_images = build_placewise_images(queries, count=4)

    # Deduplicate
    seen_urls = set()
    unique: list[dict] = []
    for img in all_images:
        if img["url"] not in seen_urls:
            seen_urls.add(img["url"])
            unique.append(img)
    return unique[:8]
