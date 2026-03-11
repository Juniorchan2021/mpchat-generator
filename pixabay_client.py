"""
MPChat v3.0 — Pixabay 免费图库 API 客户端
Free tier: 100 requests/min, no attribution required.
"""

import requests

PIXABAY_API_URL = "https://pixabay.com/api/"


def search_images(
    api_key: str,
    query: str,
    count: int = 3,
    lang: str = "en",
    image_type: str = "photo",
    orientation: str = "horizontal",
    min_width: int = 800,
) -> list[dict]:
    """
    Search Pixabay for stock photos.

    Returns list of dicts:
        {url, preview_url, alt_text, photographer, page_url, width, height}
    Returns empty list on failure or missing key.
    """
    if not api_key or not api_key.strip():
        return []

    params = {
        "key": api_key.strip(),
        "q": query[:100],
        "lang": lang,
        "image_type": image_type,
        "orientation": orientation,
        "min_width": min_width,
        "per_page": min(count, 20),
        "safesearch": "true",
        "editors_choice": "false",
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
            "width": hit.get("imageWidth", 0),
            "height": hit.get("imageHeight", 0),
        })

    return results


def build_search_queries(
    scenario_terms: list[str] | None = None,
    ai_terms: list[str] | None = None,
) -> list[str]:
    """
    Merge scenario-defined Pixabay terms with AI-suggested terms.
    Deduplicates and returns up to 5 queries.
    """
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
    api_key: str,
    scenario_terms: list[str] | None = None,
    ai_terms: list[str] | None = None,
    per_query: int = 2,
) -> list[dict]:
    """
    High-level helper: build queries, fetch images, return flat list.
    """
    if not api_key:
        return []

    queries = build_search_queries(scenario_terms, ai_terms)
    all_images: list[dict] = []

    for q in queries:
        imgs = search_images(api_key, q, count=per_query)
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
