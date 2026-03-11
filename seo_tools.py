"""
MPChat v3.0 — SEO 工具箱
slug 生成 / JSON-LD Schema / 内部链接 / 阅读统计
"""

import json
import re
import math
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# 内部链接映射表
# ══════════════════════════════════════════════════════════════════════════════

_INTERNAL_LINKS = {
    "virtual_card":       ("MP Card - 虚拟卡",       "https://mp.net/crypto-card"),
    "physical_card":      ("MP Card - 实体卡",       "https://mp.net/crypto-card"),
    "instant_settlement": ("MP Card - 即时清算",     "https://mp.net/crypto-card"),
    "multi_currency":     ("MP Card - 多币种",       "https://mp.net/crypto-card"),
    "atm_withdrawal":     ("MP Card - ATM 提现",     "https://mp.net/crypto-card"),
    "subscription_mgmt":  ("MP Card - 订阅管理",     "https://mp.net/crypto-card"),
    "e2ee":               ("MP Chat - E2EE 加密",    "https://mp.net/crypto-chat"),
    "crypto_red_packet":  ("MP Chat - 加密红包",     "https://mp.net/crypto-chat"),
    "p2p_transfer":       ("MP Chat - P2P 转账",     "https://mp.net/crypto-chat"),
    "group_mgmt":         ("MP Chat - 社群管理",     "https://mp.net/crypto-chat"),
    "file_encryption":    ("MP Chat - 文件加密",     "https://mp.net/crypto-chat"),
    "privacy_settings":   ("MP Chat - 隐私设置",     "https://mp.net/crypto-chat"),
    "compliance":         ("MP Wallet - 合规牌照",   "https://mp.net/crypto-wallet"),
    "custody":            ("MP Wallet - 资产托管",   "https://mp.net/crypto-wallet"),
    "lloyds_insurance":   ("MP Wallet - 保险保障",   "https://mp.net/crypto-wallet"),
    "fiat_onoff":         ("MP Wallet - 法币通道",   "https://mp.net/crypto-wallet"),
    "virtual_bank_acct":  ("MP Wallet - 虚拟账户",   "https://mp.net/crypto-wallet"),
    "dex_integration":    ("DeFi - DEX 交易",        "https://mp.net/crypto-wallet"),
    "rwa_investment":     ("DeFi - RWA 投资",        "https://mp.net/crypto-wallet"),
    "non_custodial":      ("DeFi - 非托管钱包",      "https://mp.net/crypto-wallet"),
    "gas_station":        ("DeFi - Gas Station",      "https://mp.net/crypto-wallet"),
    "miniapp_sdk":        ("开发者 - MiniApp SDK",   "https://mp.net/"),
    "bot_framework":      ("开发者 - Bot 框架",      "https://mp.net/"),
    "psp_capability":     ("开发者 - PSP 支付",      "https://mp.net/"),
    "payment_api":        ("开发者 - 支付 API",      "https://mp.net/"),
    "merchant_tools":     ("开发者 - 商户工具",      "https://mp.net/"),
}

_BASE_LINKS = [
    ("MPChat 官网",    "https://mp.net/"),
    ("下载 MPChat App", "https://mp.net/download"),
]


def generate_slug(title: str) -> str:
    """
    Generate a URL-friendly slug from a title.
    Handles both English and Chinese by keeping alphanumeric + hyphens.
    For Chinese titles, extracts English words and uses pinyin-style fallback.
    """
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')

    ascii_slug = re.sub(r'[^\x00-\x7f]', '', slug)
    ascii_slug = re.sub(r'-+', '-', ascii_slug).strip('-')

    if len(ascii_slug) >= 8:
        return ascii_slug[:80]

    words = re.findall(r'[a-zA-Z]+', title.lower())
    if words:
        return '-'.join(words)[:80]

    return f"mpchat-article-{datetime.now().strftime('%Y%m%d')}"


def generate_schema(
    title: str,
    description: str,
    author: str = "MPChat",
    date: str | None = None,
    image_url: str = "",
    article_url: str = "",
) -> str:
    """Generate Article JSON-LD schema markup."""
    pub_date = date or datetime.now().strftime("%Y-%m-%d")
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title[:110],
        "description": description[:300],
        "author": {
            "@type": "Organization",
            "name": author,
            "url": "https://mp.net",
        },
        "publisher": {
            "@type": "Organization",
            "name": "MPChat",
            "url": "https://mp.net",
            "logo": {
                "@type": "ImageObject",
                "url": "https://mp.net/logo.png",
            },
        },
        "datePublished": pub_date,
        "dateModified": pub_date,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": article_url or "https://mp.net/blog",
        },
    }
    if image_url:
        schema["image"] = {
            "@type": "ImageObject",
            "url": image_url,
        }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def generate_internal_links(
    selling_point_ids: list[str],
) -> list[dict]:
    """
    Suggest internal links based on selected selling points.
    Returns list of {text, url} dicts, deduplicated by URL.
    """
    seen_urls = set()
    links: list[dict] = []

    for base_text, base_url in _BASE_LINKS:
        seen_urls.add(base_url)
        links.append({"text": base_text, "url": base_url})

    for sp_id in selling_point_ids:
        if sp_id in _INTERNAL_LINKS:
            text, url = _INTERNAL_LINKS[sp_id]
            if url not in seen_urls:
                seen_urls.add(url)
                links.append({"text": text, "url": url})

    return links[:8]


def reading_stats(article_text: str, keywords: str = "") -> dict:
    """
    Analyze article for SEO readability metrics.
    Returns dict with word_count, reading_time_min, h2_count, has_cta,
    keyword_density, structure_score.
    """
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', article_text))
    en_words = len(re.findall(r'[a-zA-Z]+', article_text))
    total_words = cn_chars + en_words

    reading_time = max(1, math.ceil(total_words / 300))

    h2_count = len(re.findall(r'^##\s', article_text, re.MULTILINE))
    h1_count = len(re.findall(r'^#\s', article_text, re.MULTILINE))

    cta_patterns = [
        r'下载', r'注册', r'立即', r'申请', r'点击', r'开始',
        r'download', r'sign\s*up', r'get\s+started', r'apply',
        r'join', r'try\s+now',
    ]
    text_lower = article_text.lower()
    has_cta = any(re.search(p, text_lower) for p in cta_patterns)

    kw_density = {}
    if keywords.strip():
        kw_list = [k.strip() for k in keywords.split(',') if k.strip()]
        for kw in kw_list[:10]:
            count = text_lower.count(kw.lower())
            if total_words > 0:
                density = round(count / max(total_words, 1) * 100, 2)
            else:
                density = 0.0
            kw_density[kw] = {"count": count, "density_pct": density}

    score = 0
    if h1_count >= 1:
        score += 20
    if h2_count >= 2:
        score += 20
    elif h2_count >= 1:
        score += 10
    if has_cta:
        score += 20
    if 600 <= total_words <= 1500:
        score += 20
    elif total_words > 300:
        score += 10
    if kw_density:
        avg_density = sum(v["density_pct"] for v in kw_density.values()) / len(kw_density)
        if 0.5 <= avg_density <= 3.0:
            score += 20
        elif avg_density > 0:
            score += 10

    return {
        "word_count": total_words,
        "cn_chars": cn_chars,
        "en_words": en_words,
        "reading_time_min": reading_time,
        "h1_count": h1_count,
        "h2_count": h2_count,
        "has_cta": has_cta,
        "keyword_density": kw_density,
        "structure_score": min(score, 100),
    }
