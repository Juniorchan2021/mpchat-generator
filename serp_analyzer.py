"""
MPChat v4.0 — Lightweight SERP Analyzer
Scrape Google top 10 results for target keywords, extract patterns,
and generate content strategy recommendations for LLM injection.
"""

import re
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def search_google(query: str, num_results: int = 10) -> list[dict]:
    """Scrape Google search results (title, URL, snippet)."""
    params = {
        "q": query,
        "num": num_results,
        "hl": "en",
    }
    try:
        r = requests.get(
            "https://www.google.com/search",
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    results: list[dict] = []
    for g in soup.select("div.g, div[data-sokoban-container]"):
        link_el = g.select_one("a[href]")
        title_el = g.select_one("h3")
        snippet_el = g.select_one("div.VwiC3b, span.aCOpRe, div[data-sncf]")
        if not link_el or not title_el:
            continue
        href = link_el.get("href", "")
        if href.startswith("/url?q="):
            href = href.split("/url?q=")[1].split("&")[0]
        if not href.startswith("http"):
            continue
        results.append({
            "title": title_el.get_text(strip=True),
            "url": href,
            "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
        })
    return results[:num_results]


def fetch_page_headings(url: str) -> list[str]:
    """Fetch H1/H2 headings from a URL."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        headings = []
        for tag in soup.find_all(["h1", "h2"]):
            text = tag.get_text(strip=True)
            if text:
                headings.append(f"{tag.name.upper()}: {text}")
        return headings[:15]
    except Exception:
        return []


def analyze_serp(keyword: str, max_pages: int = 5) -> dict:
    """
    Analyze SERP for a keyword:
    1. Fetch Google top results
    2. Extract headings from top pages (parallel)
    3. Identify content patterns
    """
    results = search_google(keyword)
    if not results:
        return {
            "keyword": keyword,
            "results": [],
            "headings": [],
            "patterns": {},
            "recommendation": "无法获取 SERP 数据，请检查网络或手动搜索。",
        }

    all_headings: list[str] = []
    urls_to_fetch = [r["url"] for r in results[:max_pages]]

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch_page_headings, url): url for url in urls_to_fetch}
        for future in as_completed(futures):
            try:
                headings = future.result()
                all_headings.extend(headings)
            except Exception:
                pass

    titles = [r["title"] for r in results]
    snippets = [r["snippet"] for r in results if r["snippet"]]

    patterns = _extract_patterns(titles, snippets, all_headings)

    recommendation = _build_recommendation(keyword, patterns, results)

    return {
        "keyword": keyword,
        "results": results[:10],
        "headings": all_headings[:30],
        "patterns": patterns,
        "recommendation": recommendation,
    }


def _extract_patterns(
    titles: list[str], snippets: list[str], headings: list[str]
) -> dict:
    """Extract content patterns from SERP data."""
    all_text = " ".join(titles + snippets)

    question_count = len(re.findall(r"\?|？", all_text))
    listicle_count = len(re.findall(r"\b(?:top|best|\d+)\b", all_text, re.IGNORECASE))
    how_to_count = len(re.findall(r"\b(?:how to|guide|tutorial|步骤|教程)\b", all_text, re.IGNORECASE))
    comparison_count = len(re.findall(r"\b(?:vs\.?|versus|comparison|对比)\b", all_text, re.IGNORECASE))

    avg_title_len = sum(len(t) for t in titles) / len(titles) if titles else 0

    has_faq = any("faq" in h.lower() or "常见问题" in h for h in headings)
    has_reviews = any(
        re.search(r"review|评测|评价", h, re.IGNORECASE)
        for h in headings
    )

    common_words = _find_common_terms(titles + [h.split(": ", 1)[-1] for h in headings])

    return {
        "question_heavy": question_count >= 3,
        "listicle_heavy": listicle_count >= 3,
        "how_to_heavy": how_to_count >= 2,
        "comparison_heavy": comparison_count >= 2,
        "avg_title_length": round(avg_title_len),
        "has_faq_sections": has_faq,
        "has_review_content": has_reviews,
        "common_terms": common_words[:10],
        "total_results_analyzed": len(titles),
    }


def _find_common_terms(texts: list[str], min_count: int = 2) -> list[str]:
    """Find frequently occurring meaningful terms."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "through", "during",
        "before", "after", "above", "below", "and", "but", "or", "not",
        "no", "nor", "so", "yet", "both", "either", "neither", "each",
        "every", "all", "any", "few", "more", "most", "other", "some",
        "such", "than", "too", "very", "just", "about", "this", "that",
        "these", "those", "it", "its", "your", "my", "h1", "h2",
        "的", "了", "是", "在", "和", "与", "或", "但", "也", "都", "就",
        "不", "有", "个", "人", "中", "大", "上", "为", "被", "他", "她",
    }
    word_count: dict[str, int] = {}
    for text in texts:
        words = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
        for w in words:
            if w not in stop_words and len(w) > 1:
                word_count[w] = word_count.get(w, 0) + 1
    sorted_words = sorted(word_count.items(), key=lambda x: -x[1])
    return [w for w, c in sorted_words if c >= min_count]


def _build_recommendation(keyword: str, patterns: dict, results: list[dict]) -> str:
    """Build content strategy recommendation based on SERP patterns."""
    recs: list[str] = []

    if patterns.get("question_heavy"):
        recs.append("SERP 偏好问答式内容 — 建议使用问句标题和 FAQ 段落")
    if patterns.get("listicle_heavy"):
        recs.append("SERP 中 Top-N 清单型文章较多 — 可采用清单盘点型文风")
    if patterns.get("how_to_heavy"):
        recs.append("SERP 偏好教程型内容 — 建议采用手把手教程型文风")
    if patterns.get("comparison_heavy"):
        recs.append("SERP 中竞品对比内容较多 — 建议使用竞品对比场景")
    if patterns.get("has_faq_sections"):
        recs.append("竞品页面包含 FAQ — 强烈建议加入 FAQ 段落（GEO 加分）")
    if patterns.get("has_review_content"):
        recs.append("SERP 中有评测内容 — 可采用评测种草型文风")

    common = patterns.get("common_terms", [])
    if common:
        recs.append(f"高频词汇：{', '.join(common[:8])} — 建议在文章中覆盖这些术语")

    if len(results) < 5:
        recs.append("SERP 竞争较低 — 该关键词有较好的排名机会")

    return "\n".join(f"• {r}" for r in recs) if recs else "暂无特殊建议，按默认策略生成即可。"


def serp_to_prompt_context(serp_data: dict) -> str:
    """Convert SERP analysis into context for LLM prompt injection."""
    if not serp_data.get("results"):
        return ""

    lines = [f"【SERP 竞品分析 — 关键词：{serp_data['keyword']}】"]
    lines.append(f"Google Top {len(serp_data['results'])} 竞品标题：")
    for i, r in enumerate(serp_data["results"][:5], 1):
        lines.append(f"  {i}. {r['title']}")

    if serp_data.get("headings"):
        lines.append("\n竞品常见 H2 结构：")
        seen = set()
        for h in serp_data["headings"][:10]:
            if h not in seen:
                seen.add(h)
                lines.append(f"  - {h}")

    if serp_data.get("patterns", {}).get("common_terms"):
        terms = serp_data["patterns"]["common_terms"][:8]
        lines.append(f"\n高频关键术语：{', '.join(terms)}")

    lines.append(f"\n策略建议：\n{serp_data.get('recommendation', '')}")
    lines.append("\n请参考以上竞品数据，创作更具竞争力的内容。")

    return "\n".join(lines)
