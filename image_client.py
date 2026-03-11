"""
MPChat v4.0 — Multi-source image client
Primary: Placewise (aggregates Pixabay + Pexels + Unsplash, no API key)
Fallback: Pixabay direct API
"""

import requests

PLACEWISE_BASE = "https://placewise.io/api/v1"
PIXABAY_API_URL = "https://pixabay.com/api/"


# ── Placewise (primary) ─────────────────────────────────────────────────────

def search_placewise(
    query: str,
    count: int = 4,
    orientation: str = "landscape",
) -> list[dict]:
    """Search Placewise which aggregates Pixabay + Pexels + Unsplash."""
    if not query or not query.strip():
        return []
    url = f"{PLACEWISE_BASE}/search"
    params = {
        "query": query.strip()[:100],
        "per_page": min(count, 10),
        "orientation": orientation,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    results = []
    for item in data.get("results", data.get("photos", data.get("hits", [])))[:count]:
        results.append({
            "url": item.get("url") or item.get("src", {}).get("large") or item.get("largeImageURL", ""),
            "preview_url": item.get("thumbnail") or item.get("src", {}).get("medium") or item.get("webformatURL", ""),
            "alt_text": query,
            "photographer": item.get("photographer") or item.get("user") or "Unknown",
            "page_url": item.get("source_url") or item.get("url") or "",
            "source": item.get("source", "Placewise"),
        })
    return [r for r in results if r["url"]]


# ── Pixabay (fallback) ──────────────────────────────────────────────────────

def search_pixabay(
    api_key: str,
    query: str,
    count: int = 4,
    orientation: str = "horizontal",
    min_width: int = 800,
) -> list[dict]:
    """Direct Pixabay API search as fallback."""
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


# ── Unified search ──────────────────────────────────────────────────────────

def build_search_queries(
    scenario_terms: list[str] | None = None,
    ai_terms: list[str] | None = None,
) -> list[str]:
    """Merge and deduplicate search queries from scenario and AI suggestions."""
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
    scenario_terms: list[str] | None = None,
    ai_terms: list[str] | None = None,
    per_query: int = 2,
) -> list[dict]:
    """
    High-level image fetcher.
    Tries Placewise first (aggregates 3 sources), falls back to Pixabay.
    """
    queries = build_search_queries(scenario_terms, ai_terms)
    if not queries:
        return []

    all_images: list[dict] = []
    placewise_failed = False

    for q in queries:
        imgs = search_placewise(q, count=per_query)
        if not imgs:
            placewise_failed = True
            break
        for img in imgs:
            img["query"] = q
        all_images.extend(imgs)

    if placewise_failed and pixabay_key:
        all_images = []
        for q in queries:
            imgs = search_pixabay(pixabay_key, q, count=per_query)
            for img in imgs:
                img["query"] = q
            all_images.extend(imgs)

    seen_urls = set()
    unique: list[dict] = []
    for img in all_images:
        if img["url"] not in seen_urls:
            seen_urls.add(img["url"])
            unique.append(img)
    return unique[:8]
