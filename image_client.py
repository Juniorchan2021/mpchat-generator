"""
MPChat v4.1 — Multi-source image client
Tier 1: Pixabay (primary, API search with random page offset)
Tier 2: Pexels (secondary, free 200 req/hr, random page offset)
Tier 3: Placewise CDN (URL-based fallback, no API key)

Randomization: each call picks a random page (1-5) so repeated
generation with the same scenario returns different images.
"""

import random
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
    page = random.randint(1, 5)
    params = {
        "key": api_key.strip(),
        "q": query[:100],
        "lang": "en",
        "image_type": "photo",
        "orientation": orientation,
        "min_width": min_width,
        "per_page": min(count + 4, 20),
        "page": page,
        "safesearch": "true",
    }
    try:
        r = requests.get(PIXABAY_API_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    hits = data.get("hits", [])
    if hits:
        random.shuffle(hits)

    results = []
    for hit in hits[:count]:
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
    page = random.randint(1, 5)
    headers = {"Authorization": api_key.strip()}
    params = {
        "query": query[:100],
        "per_page": min(count + 4, 15),
        "page": page,
        "orientation": orientation,
    }
    try:
        r = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    photos = data.get("photos", [])
    if photos:
        random.shuffle(photos)

    results = []
    for photo in photos[:count]:
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
    slug = query.strip().lower().replace(" ", "-")[:80]
    return f"{PLACEWISE_CDN}/{width}x{height}-{slug}"


def build_placewise_images(queries: list[str], count: int = 4) -> list[dict]:
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
    ai_terms: list[str] | None = None,
    scenario_terms: list[str] | None = None,
    article_title: str = "",
) -> list[str]:
    """Build search queries, prioritizing AI-generated terms (article-specific)
    over static scenario terms. Optionally extract keywords from the title."""
    queries: list[str] = []
    seen: set[str] = set()

    def _add(term: str):
        key = term.strip().lower()
        if key and key not in seen and len(key) > 2:
            seen.add(key)
            queries.append(term.strip())

    for term in (ai_terms or []):
        _add(term)

    if article_title:
        title_words = [w for w in article_title.split() if len(w) > 3]
        if len(title_words) >= 2:
            _add(" ".join(title_words[:4]))

    for term in (scenario_terms or []):
        _add(term)

    return queries[:6]


def fetch_images_for_article(
    pixabay_key: str = "",
    pexels_key: str = "",
    scenario_terms: list[str] | None = None,
    ai_terms: list[str] | None = None,
    article_title: str = "",
    per_query: int = 2,
) -> list[dict]:
    """
    High-level image fetcher with 3-tier fallback and randomization.
    Each call returns different images even for the same scenario.
    """
    queries = build_search_queries(
        ai_terms=ai_terms,
        scenario_terms=scenario_terms,
        article_title=article_title,
    )
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
        remaining = max(1, per_query)
        for q in queries:
            if len(all_images) >= 8:
                break
            imgs = search_pexels(pexels_key, q, count=remaining)
            for img in imgs:
                img["query"] = q
            all_images.extend(imgs)

    # Tier 3: Placewise CDN (if both APIs failed)
    if not all_images:
        all_images = build_placewise_images(queries, count=4)

    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique: list[dict] = []
    for img in all_images:
        if img["url"] not in seen_urls:
            seen_urls.add(img["url"])
            unique.append(img)

    # Shuffle final results for variety
    random.shuffle(unique)
    return unique[:8]
