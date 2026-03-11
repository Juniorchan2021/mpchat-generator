"""
MPChat 智能软文生成器 v4.0
37+ 细分场景 · 25+ 卖点 · 7 种文风 · 16 种语言 · 多图库 · GEO + SEO 双优化
流式进度 · 批量生成 · 历史记录 · 文内配图 · A/B 标题 · 竞品对比
"""

import os
import io
import re
import json
import time
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st
import requests
import markdown as md_lib
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

from scenarios import (
    SCENARIO_CATEGORIES,
    SELLING_POINT_GROUPS,
    SP_ID_TO_LABEL,
    ARTICLE_STYLES,
    KEYWORD_PRESETS,
    LANGUAGES,
)
from image_client import fetch_images_for_article
from seo_tools import (
    generate_slug,
    generate_schema,
    generate_internal_links,
    reading_stats,
)
from geo_tools import geo_score, generate_faq_schema, build_geo_optimize_prompt, build_dual_optimize_prompt
from publishers import (
    publish_to_devto,
    publish_to_hashnode,
    format_for_medium,
    format_for_linkedin,
    format_for_twitter_thread,
    format_for_zhihu,
    format_for_wechat,
    format_for_crypto_submission,
)
from serp_analyzer import analyze_serp, serp_to_prompt_context

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# AI 服务商预设
# ══════════════════════════════════════════════════════════════════════════════
PROVIDERS = {
    "🟢 Google Gemini（免费推荐）": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-001"],
        "key_prefix": "AIzaSy...",
        "get_key_url": "https://aistudio.google.com/apikey",
    },
    "🔵 OpenAI": {
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "key_prefix": "sk-...",
        "get_key_url": "https://platform.openai.com/api-keys",
    },
    "🟣 DeepSeek（高性价比）": {
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "key_prefix": "sk-...",
        "get_key_url": "https://platform.deepseek.com/api_keys",
    },
    "🟡 Kimi（月之暗面）": {
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-128k", "moonshot-v1-32k", "moonshot-v1-8k"],
        "key_prefix": "sk-...",
        "get_key_url": "https://platform.moonshot.cn/console/api-keys",
    },
    "🟠 OpenRouter（支持全部模型）": {
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "anthropic/claude-sonnet-4",
            "google/gemini-2.5-flash",
            "openai/gpt-4o",
            "deepseek/deepseek-chat",
        ],
        "key_prefix": "sk-or-...",
        "get_key_url": "https://openrouter.ai/keys",
    },
    "⚙️ 自定义（手动填写）": {
        "base_url": "",
        "models": [],
        "key_prefix": "",
        "get_key_url": "",
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# 网络抓取
# ══════════════════════════════════════════════════════════════════════════════
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}


def _fetch_html(url: str, max_chars: int = 3000) -> str:
    try:
        r = requests.get(url, headers=HTTP_HEADERS, timeout=12, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header",
                          "aside", "form", "noscript", "svg", "img", "iframe"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return "\n".join(lines)[:max_chars]
    except Exception as e:
        return f"[抓取失败: {e}]"


def _fetch_medium_rss(max_items: int = 5, max_chars: int = 3000) -> str:
    rss_url = "https://medium.com/feed/@mpchat_blog"
    try:
        r = requests.get(rss_url, headers=HTTP_HEADERS, timeout=12)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        items = root.findall(".//item")[:max_items]
        parts = []
        for item in items:
            title = item.findtext("title", "")
            desc_raw = item.findtext("description", "")
            soup = BeautifulSoup(desc_raw, "html.parser")
            desc = soup.get_text(strip=True)[:500]
            parts.append(f"📝 {title}\n{desc}")
        return "\n\n".join(parts)[:max_chars]
    except Exception as e:
        return f"[抓取失败: {e}]"


def _fetch_search(engine: str, query: str, max_chars: int = 2500) -> str:
    if engine == "google":
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=8&hl=zh-CN"
    elif engine == "baidu":
        url = f"https://www.baidu.com/s?wd={requests.utils.quote(query)}&rn=8"
    elif engine == "duckduckgo":
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
    else:
        return "[不支持的搜索引擎]"
    try:
        headers = {**HTTP_HEADERS}
        if engine == "google":
            headers["Accept-Language"] = "zh-CN,zh;q=0.9,en;q=0.8"
        r = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header",
                          "aside", "form", "noscript", "svg", "img", "iframe"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [ln.strip() for ln in text.splitlines()
                 if ln.strip() and len(ln.strip()) > 15]
        return "\n".join(lines)[:max_chars]
    except Exception as e:
        return f"[抓取失败: {e}]"


def _fetch_nitter_twitter(max_chars: int = 2000) -> str:
    nitter_instances = [
        "https://nitter.net/MPChatApp",
        "https://nitter.privacydev.net/MPChatApp",
        "https://nitter.poast.org/MPChatApp",
    ]
    for nitter_url in nitter_instances:
        try:
            r = requests.get(nitter_url, headers=HTTP_HEADERS, timeout=8,
                             allow_redirects=True)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                tweets = soup.select(".tweet-content, .timeline-item .tweet-body")
                if tweets:
                    parts = [t.get_text(strip=True)[:300] for t in tweets[:10]]
                    return "\n\n".join(parts)[:max_chars]
        except Exception:
            continue
    return "[抓取失败: Twitter/X 暂不可直接抓取]"


@st.cache_data(ttl=7200, show_spinner=False)
def fetch_web_knowledge() -> tuple[str, list[dict]]:
    tasks = [
        ("🌐 官网 mp.net", lambda: _fetch_html("https://mp.net/", 3000)),
        ("💰 MP Wallet 页面", lambda: _fetch_html("https://mp.net/crypto-wallet", 2500)),
        ("💬 MP Chat 页面", lambda: _fetch_html("https://mp.net/crypto-chat", 2500)),
        ("💳 MP Card 页面", lambda: _fetch_html("https://mp.net/crypto-card", 2500)),
        ("📝 Medium 博客 (RSS)", lambda: _fetch_medium_rss(5, 3000)),
        ("🐦 Twitter @MPChatApp", lambda: _fetch_nitter_twitter(2000)),
        ("🔍 Google 搜索", lambda: _fetch_search("google", "MPChat mp.net crypto card stablecoin payment", 2500)),
        ("🔍 百度搜索", lambda: _fetch_search("baidu", "MPChat mp.net 加密支付卡 稳定币", 2500)),
        ("🔍 DuckDuckGo 搜索", lambda: _fetch_search("duckduckgo", "MPChat mp.net crypto card payment wallet", 2500)),
        ("📰 GlobeNewswire 新闻稿",
         lambda: _fetch_html(
             "https://www.globenewswire.com/news-release/2025/10/27/3174941/0/en/"
             "MPChat-Announces-Binance-Pay-Integration-Unlocking-a-New-Era-of-"
             "Seamless-Crypto-Top-Ups-for-Global-Users.html", 2500)),
    ]

    results_map: dict[str, dict] = {}
    texts_map: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=10) as pool:
        future_to_label = {}
        for label, fn in tasks:
            future_to_label[pool.submit(fn)] = (label, time.time())

        for future in as_completed(future_to_label):
            label, t0 = future_to_label[future]
            elapsed = round(time.time() - t0, 1)
            try:
                text = future.result()
            except Exception as e:
                text = f"[抓取失败: {e}]"
            ok = not text.startswith("[抓取失败")
            results_map[label] = {"label": label, "ok": ok, "elapsed": elapsed}
            if ok and len(text.strip()) > 50:
                texts_map[label] = text

    results = []
    all_text_parts = []
    for label, _ in tasks:
        if label in results_map:
            results.append(results_map[label])
        if label in texts_map:
            all_text_parts.append(f"### 来源：{label}\n{texts_map[label]}")

    combined = "\n\n---\n\n".join(all_text_parts)
    return combined, results


# ══════════════════════════════════════════════════════════════════════════════
# 知识库
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_knowledge():
    kb_path = os.path.join(os.path.dirname(__file__), "knowledge.txt")
    if os.path.exists(kb_path):
        with open(kb_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


KNOWLEDGE = load_knowledge()

# ══════════════════════════════════════════════════════════════════════════════
# LLM 调用
# ══════════════════════════════════════════════════════════════════════════════

def get_client(api_key: str, base_url: str) -> OpenAI:
    kwargs = {"api_key": api_key}
    if base_url.strip():
        kwargs["base_url"] = base_url.strip()
    return OpenAI(**kwargs)


def _geo_prompt_section() -> str:
    return """

【GEO 优化规范 — Generative Engine Optimization】
当前已启用 GEO 模式。请在 SEO 规范基础上额外遵守以下规则：
- Answer-First：文章开头 40-100 字必须直接回答核心问题，不要铺垫
- 问题式标题：至少 30% 的 H2 副标题使用问句（如 "MPChat 的安全性如何保障？"）
- 数据引用：在文章中插入 5+ 个带出处的统计数据（如 "据 Chainalysis 2025 报告..."）
- FAQ 段落：在文末加入 5 个 Q&A 对，每个答案 < 100 字
- 短段落：每段 2-3 句，适合 AI 摘要提取
- 权威引用：使用 "据...研究显示" 框架提升可信度
- 实体一致性：全文统一使用 MPChat / MP Card / MP Wallet 等正式名称
- 在 JSON 输出中额外增加字段 "faq_pairs": [{"q":"问题","a":"回答"},...]（5 对）
"""


def build_system_prompt(language: str, style_instruction: str,
                        scenario_label: str, web_content: str = "",
                        geo_mode: bool = False) -> str:
    lang_cfg = LANGUAGES.get(language, LANGUAGES["中文 (Chinese)"])
    lang_instruction = lang_cfg["instruction"]
    web_section = (
        f"\n\n【实时网络资料（来自 mp.net 官网 / Medium / Twitter / Google / 百度）】\n{web_content[:8000]}"
        if web_content.strip() else ""
    )
    return f"""你是 MPChat 的顶级内容营销专家，专精 SEO 内容策略、加密金融科普写作和 AI 绘画提示词（Prompt）工程。

{lang_instruction}

【产品知识库（内部文档）】
{KNOWLEDGE}{web_section}

【当前写作场景】
{scenario_label}

【文风要求】
{style_instruction}

【你的核心职责】
基于用户提供的参数，创作一篇兼顾 SEO 优化和用户体验的高质量推广软文，并产出专业的 AI 绘画提示词和 Pixabay 图片搜索关键词。

【SEO 写作规范】
- 文章必须包含 H1（主标题，用 # 表示）、H2（副标题，用 ## 表示）、H3（可选，用 ### 表示）
- 自然植入用户指定的 SEO 关键词，不堆砌，保持阅读流畅
- 每段不超过 150 字，适合移动端阅读
- 文章总长度：800-1200 字（中文）/ 600-900 词（英文）
- 结尾必须有清晰有力的 CTA（Call to Action），引导用户下载 MPChat 或申请 MP Card

【输出格式要求（严格遵守 JSON 格式）】
请以合法的 JSON 格式输出，结构如下：
{{
  "seo_title": "文章 SEO 标题（50-60 字符，含核心关键词）",
  "meta_description": "元描述（120-160 字符，总结文章价值并含关键词）",
  "slug_suggestion": "url-friendly-slug-in-english",
  "title_alternatives": ["备选标题1（不同角度）", "备选标题2（不同风格）", "备选标题3（不同卖点）"],
  "article": "完整文章正文（Markdown 格式，含 H1/H2/CTA）",
  "image_prompts": [
    {{
      "scene": "场景描述（中文）",
      "prompt": "英文 Midjourney/DALL-E 提示词（详细、专业、含风格/光线/构图）"
    }}
  ],
  "image_search_terms": ["英文Pixabay搜索词1", "英文搜索词2", "英文搜索词3"]
}}

【title_alternatives 规范】
- 提供 3 个与主标题不同角度的备选标题，供 A/B 测试使用
- 每个标题都要包含核心关键词，但切入角度不同（如：数据型、疑问型、利益型）
- 长度同样控制在 50-60 字符

【Image Prompt 规范】
- 必须是纯英文
- 必须包含：主体描述 + 环境背景 + 光影效果 + 艺术风格 + 质量标签
- 生成 2-3 个不同场景的 Prompt
- 禁止出现品牌 Logo 或真实人脸描写

【image_search_terms 规范】
- 提供 3-5 个英文关键词，用于在 Pixabay 搜索配图
- 关键词要具体、视觉化（如 "digital payment smartphone" 而非 "crypto"）
""" + (_geo_prompt_section() if geo_mode else "")


def build_user_prompt(language, scenario_label, audience_tag,
                      selling_points_text, style_name, keywords):
    kw_str = keywords.strip() if keywords.strip() else "MPChat, 加密支付, 稳定币"
    return f"""请根据以下参数，生成一篇完整的 MPChat 推广软文和配套 AI 绘画提示词。

【生成参数】
- 输出语言：{language}
- 写作场景：{scenario_label}
- 目标受众：{audience_tag}
- 主打卖点：{selling_points_text}
- 文章文风：{style_name}
- SEO 核心关键词：{kw_str}

请严格按照系统提示中规定的 JSON 格式输出，确保 JSON 合法可解析。
"""


def _extract_json_field(raw: str, field: str) -> str | None:
    """Extract a string field value from raw JSON text using regex (handles truncated JSON)."""
    pattern = rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"'
    m = re.search(pattern, raw, re.DOTALL)
    if m:
        val = m.group(1)
        val = val.replace('\\n', '\n').replace('\\t', '\t')
        val = val.replace('\\"', '"').replace('\\\\', '\\')
        return val
    return None


def _extract_json_array(raw: str, field: str) -> list[str] | None:
    """Extract a string array field from raw JSON text."""
    pattern = rf'"{field}"\s*:\s*\[(.*?)\]'
    m = re.search(pattern, raw, re.DOTALL)
    if m:
        return re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
    return None


def _robust_parse(raw: str) -> dict:
    """Try multiple strategies to parse JSON from LLM output."""
    # Strategy 1: direct parse
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 2: fix trailing commas
    fixed = re.sub(r',\s*}', '}', raw)
    fixed = re.sub(r',\s*]', ']', fixed)
    try:
        return json.loads(fixed)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 3: collapse real newlines that break JSON string values
    try:
        collapsed = raw.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
        return json.loads(collapsed)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 4: regex extraction (handles truncated / malformed JSON)
    article = _extract_json_field(raw, 'article')
    if article:
        result: dict = {"article": article}
        for fld in ('seo_title', 'meta_description', 'slug_suggestion'):
            val = _extract_json_field(raw, fld)
            if val:
                result[fld] = val
        ta = _extract_json_array(raw, 'title_alternatives')
        if ta:
            result["title_alternatives"] = ta
        ist = _extract_json_array(raw, 'image_search_terms')
        if ist:
            result["image_search_terms"] = ist
        result.setdefault("seo_title", "MPChat — Live with Crypto")
        result.setdefault("meta_description", "")
        result.setdefault("slug_suggestion", "mpchat-article")
        result.setdefault("image_prompts", [])
        result.setdefault("image_search_terms", ["crypto payment", "digital finance"])
        result.setdefault("title_alternatives", [])
        return result

    # Strategy 5: last resort — clean raw text and use as article
    cleaned = raw
    if '"article"' in cleaned:
        a_start = cleaned.find('"article"')
        colon = cleaned.find(':', a_start + 9)
        if colon >= 0:
            q_start = cleaned.find('"', colon)
            if q_start >= 0:
                cleaned = cleaned[q_start + 1:]
                for end_marker in ('"image_prompts"', '"image_search_terms"',
                                   '"title_alternatives"'):
                    eidx = cleaned.find(end_marker)
                    if eidx > 0:
                        cleaned = cleaned[:cleaned.rfind('"', 0, eidx)].strip()
                        break
    cleaned = cleaned.replace('\\n', '\n').replace('\\t', '\t')
    cleaned = cleaned.replace('\\"', '"').replace('\\\\', '\\')
    return {
        "seo_title": _extract_json_field(raw, 'seo_title') or "MPChat — Live with Crypto",
        "meta_description": _extract_json_field(raw, 'meta_description') or "",
        "slug_suggestion": _extract_json_field(raw, 'slug_suggestion') or "mpchat-article",
        "article": cleaned,
        "image_prompts": [],
        "image_search_terms": _extract_json_array(raw, 'image_search_terms') or ["crypto payment"],
        "title_alternatives": _extract_json_array(raw, 'title_alternatives') or [],
    }


def generate_article(client, model, language, scenario_label, audience_tag,
                     selling_points_text, style_name, style_instruction,
                     keywords, web_content="", geo_mode=False):
    system_prompt = build_system_prompt(language, style_instruction,
                                        scenario_label, web_content,
                                        geo_mode=geo_mode)
    user_prompt = build_user_prompt(language, scenario_label, audience_tag,
                                    selling_points_text, style_name, keywords)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.82,
            max_tokens=16384,
            response_format={"type": "json_object"},
        )
    except Exception:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.82,
            max_tokens=16384,
        )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        inner = "\n".join(lines[1:])
        if "```" in inner:
            raw = inner[:inner.rfind("```")].strip()
        else:
            raw = inner.strip()

    if not raw.startswith("{"):
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            raw = match.group(0)

    return _robust_parse(raw)


def insert_images_into_article(article_text: str, images: list[dict],
                                max_inserts: int = 3) -> str:
    """Insert Pixabay images into article after H2 headings."""
    if not images:
        return article_text
    lines = article_text.split('\n')
    h2_indices = [i for i, ln in enumerate(lines) if ln.strip().startswith('## ')]
    if len(h2_indices) >= 2:
        positions = h2_indices[1::2][:max_inserts]
    elif h2_indices:
        positions = [h2_indices[0]]
    else:
        return article_text
    offset = 0
    for idx, pos in enumerate(positions):
        if idx >= len(images):
            break
        img = images[idx]
        img_md = (
            f"\n![{img['alt_text']}]({img['url']})\n"
            f"*📷 {img['photographer']} via [{img.get('source', 'Pixabay')}]({img['page_url']})*\n"
        )
        lines.insert(pos + 1 + offset, img_md)
        offset += 1
    return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# Streamlit 页面配置 + 全局样式
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="MPChat 智能软文生成器 v4.0",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ═══ Stripe × Apple Dark Theme ═══ */

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
                 "Helvetica Neue", Arial, sans-serif;
    background-color: #09090B;
    color: #FAFAFA;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {
    background: transparent !important;
    backdrop-filter: none !important;
}
[data-testid="collapsedControl"] {
    visibility: visible !important;
    color: #A1A1AA !important;
}

.stApp {
    background-color: #09090B;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99,91,255,0.12), transparent),
        radial-gradient(ellipse 60% 40% at 80% 0%, rgba(0,150,255,0.06), transparent);
}

/* ── Banner ── */
.mp-banner {
    background: rgba(17,17,21,0.7);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 32px;
    display: flex; align-items: center; gap: 24px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06);
    backdrop-filter: blur(20px);
    position: relative;
    overflow: hidden;
}
.mp-banner::before {
    content: '';
    position: absolute;
    top: -60%; left: -30%; width: 160%; height: 200%;
    background: radial-gradient(circle at 30% 50%, rgba(99,91,255,0.10), transparent 55%);
    z-index: 0; pointer-events: none;
}
.mp-banner > div { position: relative; z-index: 1; }
.mp-banner img.mp-logo { height: 44px; width: auto; }
.mp-banner h1 {
    font-size: 2rem; font-weight: 700; margin: 0; letter-spacing: -0.03em;
    background: linear-gradient(135deg, #FFFFFF 0%, #635BFF 50%, #0096FF 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.mp-banner p { color: #A1A1AA; font-size: 0.95rem; margin: 6px 0 0 0; font-weight: 400; letter-spacing: -0.01em; }
.mp-badge {
    background: rgba(99,91,255,0.08);
    border: 1px solid rgba(99,91,255,0.25);
    color: #635BFF;
    border-radius: 20px; padding: 4px 14px; font-size: 0.7rem;
    font-weight: 600; display: inline-block; margin-top: 12px;
    letter-spacing: 0.08em; text-transform: uppercase;
}

/* ── Frosted Glass Cards ── */
div[data-testid="stVerticalBlock"] > div[style*="border"] {
    background: rgba(17,17,21,0.8) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 14px !important;
    padding: 24px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
    backdrop-filter: blur(16px) !important;
    transition: border-color 0.2s ease;
}
div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
    border-color: rgba(99,91,255,0.15) !important;
}

/* ── Typography ── */
.stMarkdown p { color: #D4D4D8; }
.stMarkdown strong { color: #FAFAFA; font-weight: 600; letter-spacing: -0.01em; }
.stCaption { color: #71717A !important; font-size: 0.82rem !important; margin-bottom: 6px !important; }

/* ── Buttons ── */
.stButton > button[kind="primary"],
.stButton > button:first-child {
    background: linear-gradient(180deg, #635BFF 0%, #5046E5 100%);
    color: #fff; font-weight: 600; border: none;
    border-radius: 8px; padding: 10px 22px; transition: all 0.15s ease;
    box-shadow: 0 2px 12px rgba(99,91,255,0.25), inset 0 1px 0 rgba(255,255,255,0.15);
    letter-spacing: 0.01em;
}
.stButton > button[kind="primary"]:hover,
.stButton > button:first-child:hover {
    background: linear-gradient(180deg, #7C75FF 0%, #635BFF 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(99,91,255,0.35), inset 0 1px 0 rgba(255,255,255,0.15);
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.04);
    color: #E4E4E7; font-weight: 500;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px; transition: all 0.15s ease;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.08);
    border-color: rgba(255,255,255,0.15);
}

/* ── Inputs ── */
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {
    background-color: rgba(0,0,0,0.3) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #FAFAFA !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within, .stTextArea textarea:focus {
    border-color: #635BFF !important;
    box-shadow: 0 0 0 2px rgba(99,91,255,0.2) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0C0C0F !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
    min-width: 310px !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 1.5rem !important;
}
.sidebar-section {
    font-size: 0.7rem; font-weight: 600; color: #71717A;
    text-transform: uppercase; letter-spacing: 0.1em;
    margin: 4px 0 12px 0; padding: 0;
}
.sidebar-logo { height: 28px; width: auto; margin-bottom: 4px; }
.sidebar-footer {
    color: #52525B; font-size: 0.72rem; text-align: center;
    padding: 12px 0 8px 0; letter-spacing: 0.02em;
}

/* ── Tabs (Stripe pill style) ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: rgba(255,255,255,0.03);
    border-radius: 10px; padding: 3px; gap: 2px;
    border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 8px; color: #71717A;
    padding: 8px 16px; font-weight: 500; font-size: 0.85rem;
    transition: all 0.15s ease;
}
.stTabs [data-baseweb="tab"]:hover { color: #A1A1AA; }
.stTabs [aria-selected="true"] {
    background-color: rgba(99,91,255,0.12) !important;
    color: #FAFAFA !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }

/* ── Checkboxes & Toggles ── */
.stCheckbox label span { color: #D4D4D8 !important; font-size: 0.88rem; }

/* ── Dividers ── */
hr { border-color: rgba(255,255,255,0.06) !important; margin: 20px 0 !important; }

/* ── Keyword Badges ── */
.kw-badge {
    display: inline-block; padding: 3px 10px; border-radius: 6px;
    font-size: 0.72rem; font-weight: 600; margin-left: 4px;
}
.kw-low  { background: rgba(34,197,94,0.08); color: #4ADE80; border: 1px solid rgba(74,222,128,0.15); }
.kw-med  { background: rgba(234,179,8,0.08); color: #FACC15; border: 1px solid rgba(250,204,21,0.15); }
.kw-high { background: rgba(239,68,68,0.08); color: #F87171; border: 1px solid rgba(248,113,113,0.15); }

/* ── Score Ring ── */
.score-ring {
    display: inline-flex; align-items: center; justify-content: center;
    width: 60px; height: 60px; border-radius: 50%;
    font-size: 1.3rem; font-weight: 700;
    background: rgba(0,0,0,0.4);
    box-shadow: inset 0 0 0 3px currentColor;
}

/* ── Radio pills in sidebar ── */
[data-testid="stSidebar"] .stRadio > div {
    gap: 4px !important;
}
[data-testid="stSidebar"] .stRadio label {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px; padding: 8px 12px;
    transition: all 0.15s ease;
}
[data-testid="stSidebar"] .stRadio label:hover {
    border-color: rgba(99,91,255,0.2);
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Banner
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="mp-banner">
  <div><img class="mp-logo" src="https://mp.net/Logo.png" alt="MP" /></div>
  <div>
    <h1>MPChat 智能软文生成器</h1>
    <p>37+ 场景 · 25+ 卖点 · 16 种语言 · 多图库 · GEO + SEO 双优化 · 多平台分发</p>
    <span class="mp-badge">v4.0 — Live with Crypto</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 侧边栏
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<img class="sidebar-logo" src="https://mp.net/Logo.png" alt="MP" />',
        unsafe_allow_html=True,
    )

    # ── AI 服务商 ─────────────────────────────────────────────────────────────
    st.markdown('<p class="sidebar-section">AI 服务商</p>', unsafe_allow_html=True)

    provider_name = st.selectbox(
        "选择 AI 服务商", options=list(PROVIDERS.keys()), index=0,
        help="选择后会自动填充 Base URL 和推荐模型",
    )
    provider = PROVIDERS[provider_name]

    def _get_default_key():
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
        return os.getenv("OPENAI_API_KEY", "")

    env_key = _get_default_key()
    api_key_input = st.text_input(
        "API Key", value=env_key, type="password",
        placeholder=provider["key_prefix"] or "输入 API Key",
    )
    if provider["get_key_url"]:
        st.caption(f"[获取 Key → {provider_name.split('（')[0].strip()}]({provider['get_key_url']})")

    env_url = os.getenv("OPENAI_BASE_URL", "")
    default_url = env_url if env_url else provider["base_url"]
    base_url_input = st.text_input(
        "Base URL", value=default_url,
        help="已根据服务商自动填充，一般无需修改",
    )

    env_model = os.getenv("OPENAI_MODEL", "")
    if provider["models"]:
        model_input = st.selectbox("模型", options=provider["models"], index=0,
                                   help="推荐使用列表中的第一个模型")
    else:
        model_input = st.text_input("模型名称", value=env_model or "",
                                    placeholder="手动输入模型名")

    st.divider()

    # ── 优化模式 ──────────────────────────────────────────────────────────────
    st.markdown('<p class="sidebar-section">优化模式</p>', unsafe_allow_html=True)
    opt_mode = st.radio(
        "优化模式",
        ["SEO 模式", "SEO + GEO 双优化"],
        index=0,
        label_visibility="collapsed",
        help="GEO = Generative Engine Optimization，优化 AI 搜索引擎（ChatGPT / Perplexity / Gemini）的可见性",
    )
    geo_mode = opt_mode == "SEO + GEO 双优化"

    st.divider()

    # ── 配图 ──────────────────────────────────────────────────────────────────
    st.markdown('<p class="sidebar-section">配图</p>', unsafe_allow_html=True)
    use_images = st.toggle("获取配图（Pixabay + Pexels + Placewise）", value=True,
                           help="Pixabay 为主图源，Pexels 补充，Placewise CDN 兜底")
    pixabay_key = ""
    pexels_key = ""
    if use_images:
        pixabay_key = st.text_input(
            "Pixabay API Key",
            value=os.getenv("PIXABAY_API_KEY", "46561407-37c6214d0e52dffc32a430eb3"),
            type="password",
            placeholder="从 pixabay.com/api/docs 获取",
        )
        def _get_pexels_key():
            if "PEXELS_API_KEY" in st.secrets:
                return st.secrets["PEXELS_API_KEY"]
            return os.getenv("PEXELS_API_KEY", "")

        pexels_key = st.text_input(
            "Pexels API Key",
            value=_get_pexels_key(),
            type="password",
            placeholder="从 pexels.com/api 获取",
        )

    st.divider()

    # ── 数据源 ────────────────────────────────────────────────────────────────
    st.markdown('<p class="sidebar-section">数据源</p>', unsafe_allow_html=True)
    use_serp = st.toggle("SERP 分析 · Google Top 10", value=False,
                         help="爬取目标关键词的 Google 排名前 10 页面，提取内容策略注入 AI Prompt")
    use_web = st.toggle("网络知识库 · 全网抓取", value=True,
                        help="官网 + Medium + Twitter + Google + 百度（点击生成时抓取，缓存 2 小时）")

    st.divider()

    # ── 多平台分发 ────────────────────────────────────────────────────────────
    st.markdown('<p class="sidebar-section">多平台分发</p>', unsafe_allow_html=True)
    devto_key = st.text_input("Dev.to API Key", type="password",
                              value=os.getenv("DEVTO_API_KEY", ""),
                              placeholder="从 dev.to/settings/extensions 获取")
    hashnode_token = st.text_input("Hashnode Token", type="password",
                                   value=os.getenv("HASHNODE_TOKEN", ""),
                                   placeholder="从 hashnode.com/settings/developer 获取")
    hashnode_pub_id = st.text_input("Hashnode Publication ID",
                                    value=os.getenv("HASHNODE_PUB_ID", ""),
                                    placeholder="从 Hashnode 博客设置获取")

    st.divider()
    st.markdown(
        '<div class="sidebar-footer">'
        '<img src="https://mp.net/Logo.png" style="height:16px;width:auto;opacity:0.4;margin-bottom:4px;" /><br/>'
        'MPChat Generator v4.0<br/>Live with Crypto</div>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# 主区域 — 配置面板
# ══════════════════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown("**📝 内容配置**")
    col_lang, col_cat, col_scen, col_style = st.columns(4)

    with col_lang:
        st.caption("🌐 输出语言")
        lang_options = list(LANGUAGES.keys())
        language = st.selectbox("输出语言", lang_options, index=0, label_visibility="collapsed")

    with col_cat:
        st.caption("🎯 场景分类")
        category_names = list(SCENARIO_CATEGORIES.keys())
        selected_category = st.selectbox("场景分类", category_names, index=0, label_visibility="collapsed")
        scenarios_in_cat = SCENARIO_CATEGORIES[selected_category]
        scenario_labels = [s["label"] for s in scenarios_in_cat]

    with col_scen:
        st.caption("📄 具体场景")
        selected_scenario_label = st.selectbox("具体场景", scenario_labels, index=0, label_visibility="collapsed")
        selected_scenario = next(s for s in scenarios_in_cat if s["label"] == selected_scenario_label)

    with col_style:
        st.caption("✍️ 文章文风")
        style_hint = selected_scenario.get("style_hint", "pain_story")
        style_keys = list(ARTICLE_STYLES.keys())
        hint_index = 0
        for i, k in enumerate(style_keys):
            if ARTICLE_STYLES[k]["id"] == style_hint:
                hint_index = i
                break
        selected_style_key = st.selectbox(
            "文风",
            style_keys,
            index=hint_index,
            label_visibility="collapsed",
            format_func=lambda k: f"{k}",
        )
        style_obj = ARTICLE_STYLES[selected_style_key]

with st.container(border=True):
    st.markdown("**💎 主打卖点 (可多选)**")
    auto_sp = set(selected_scenario.get("selling_points", []))
    if "sp_overrides" not in st.session_state:
        st.session_state["sp_overrides"] = {}

    selected_sp_ids: list[str] = []
    sp_cols = st.columns(len(SELLING_POINT_GROUPS))
    for i, (group_name, items) in enumerate(SELLING_POINT_GROUPS.items()):
        with sp_cols[i]:
            st.caption(f"{group_name}")
            for sp_id, sp_label in items.items():
                default_val = sp_id in auto_sp
                override_key = f"sp_{sp_id}"
                checked = st.checkbox(sp_label, value=default_val, key=override_key)
                if checked:
                    selected_sp_ids.append(sp_id)

    selling_points_text = "、".join(
        SP_ID_TO_LABEL.get(sid, sid) for sid in selected_sp_ids
    ) if selected_sp_ids else "MPChat 全功能"

with st.container(border=True):
    st.markdown("**🔍 SEO 关键词**")
    st.caption("点击预设快速填充，或手动编辑（将被自然植入文章正文，提升 SEO 表现）")

    preset_cols = st.columns(len(KEYWORD_PRESETS))
    for i, preset in enumerate(KEYWORD_PRESETS):
        with preset_cols[i]:
            if st.button(f"{preset['label']}", key=f"kw_preset_{i}", use_container_width=True):
                st.session_state["keywords_val"] = preset["keywords"]

    scenario_kw = selected_scenario.get("keywords", "")
    default_kw = st.session_state.get("keywords_val", scenario_kw)

    keywords = st.text_area(
        "关键词（3-5个）",
        value=default_kw,
        height=60,
        label_visibility="collapsed",
    )

# ══════════════════════════════════════════════════════════════════════════════
# 生成按钮
# ══════════════════════════════════════════════════════════════════════════════

sp_summary = ", ".join(SP_ID_TO_LABEL.get(sid, sid).split("（")[0] for sid in selected_sp_ids[:4]) or "（请选择卖点）"
if len(selected_sp_ids) > 4:
    sp_summary += f" +{len(selected_sp_ids) - 4}"

st.markdown(
    f"<div style='text-align:center; color:#6b7280; font-size:0.9rem; margin-bottom:16px;'>"
    f"<b>当前配置</b> · {language} · {selected_scenario_label} · {style_obj['id']} · 卖点: {sp_summary}"
    f"</div>",
    unsafe_allow_html=True
)

generate_btn = st.button("🚀 立即生成高转化软文", type="primary", use_container_width=True)

st.divider()


# ── 📦 批量生成 ──────────────────────────────────────────────────────────────
with st.expander("📦 批量生成模式", expanded=False):
    st.caption("选择多个场景一次性生成，完成后打包下载")
    _all_scenario_opts: list[str] = []
    _scenario_lookup: dict[str, dict] = {}
    for _cat_name, _scenarios_list in SCENARIO_CATEGORIES.items():
        for _s in _scenarios_list:
            _lbl = f"{_cat_name}  {_s['label']}"
            _all_scenario_opts.append(_lbl)
            _scenario_lookup[_lbl] = _s
    batch_selected = st.multiselect(
        "选择场景（可多选）", _all_scenario_opts,
        placeholder="点击选择要批量生成的场景...",
    )
    batch_btn = st.button(
        "🚀 批量生成", disabled=not batch_selected,
        use_container_width=True, key="batch_gen_btn",
    )
    if batch_btn and batch_selected:
        if not api_key_input.strip():
            st.error("❌ 请在左侧填写 API Key。")
        else:
            batch_results: list[dict] = []
            with st.status(
                f"📦 批量生成中（共 {len(batch_selected)} 篇）...",
                expanded=True,
            ) as bstatus:
                bclient = get_client(api_key_input, base_url_input)
                bweb = ""
                if use_web:
                    st.write("🌐 抓取网络资料...")
                    bweb, _ = fetch_web_knowledge()
                bmodel = model_input.strip() if model_input else "gemini-2.5-flash"
                for bi, blabel in enumerate(batch_selected):
                    bsc = _scenario_lookup[blabel]
                    st.write(f"📝 [{bi + 1}/{len(batch_selected)}] {bsc['label']}...")
                    bsp_text = "、".join(
                        SP_ID_TO_LABEL.get(sid, sid)
                        for sid in bsc.get("selling_points", [])
                    ) or "MPChat 全功能"
                    bstyle_hint = bsc.get("style_hint", "pain_story")
                    bstyle_key = next(
                        (k for k, v in ARTICLE_STYLES.items()
                         if v["id"] == bstyle_hint),
                        list(ARTICLE_STYLES.keys())[0],
                    )
                    bstyle_obj = ARTICLE_STYLES[bstyle_key]
                    try:
                        br = generate_article(
                            client=bclient, model=bmodel, language=language,
                            scenario_label=bsc["label"],
                            audience_tag=bsc.get("audience_tag", ""),
                            selling_points_text=bsp_text,
                            style_name=bstyle_key,
                            style_instruction=bstyle_obj["instruction"],
                            keywords=bsc.get("keywords", ""),
                            web_content=bweb,
                            geo_mode=geo_mode,
                        )
                        batch_results.append(
                            {"scenario": bsc, "result": br, "ok": True}
                        )
                    except Exception as be:
                        batch_results.append(
                            {"scenario": bsc, "error": str(be), "ok": False}
                        )
                ok_cnt = sum(1 for x in batch_results if x["ok"])
                bstatus.update(
                    label=f"✅ 批量完成 {ok_cnt}/{len(batch_results)} 篇",
                    state="complete",
                )
            st.session_state["batch_results"] = batch_results

    if st.session_state.get("batch_results"):
        bresults = st.session_state["batch_results"]
        for bi, br in enumerate(bresults):
            if br["ok"]:
                btitle = br["result"].get("seo_title", br["scenario"]["label"])
                with st.expander(f"✅ {btitle}", expanded=False):
                    st.markdown(br["result"].get("article", "")[:800] + "...")
            else:
                st.error(f"❌ {br['scenario']['label']}: {br['error']}")
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for br in bresults:
                if br["ok"]:
                    bslug = br["result"].get("slug_suggestion", "article")
                    bcontent = (
                        f"# {br['result'].get('seo_title', '')}\n\n"
                        f"> {br['result'].get('meta_description', '')}"
                        f"\n\n---\n\n"
                        f"{br['result'].get('article', '')}"
                    )
                    zf.writestr(f"{bslug}.md", bcontent.encode("utf-8"))
        st.download_button(
            f"📥 下载全部 {sum(1 for x in bresults if x['ok'])} 篇 (ZIP)",
            zip_buf.getvalue(), "mpchat-batch.zip", "application/zip",
            use_container_width=True, key="batch_download",
        )

# ══════════════════════════════════════════════════════════════════════════════
# 单篇生成逻辑
# ══════════════════════════════════════════════════════════════════════════════
if generate_btn:
    if not api_key_input.strip():
        st.error("❌ 请在左侧填写 API Key。")
        st.stop()
    if not selected_sp_ids:
        st.warning("⚠️ 请至少选择一个主打卖点。")
        st.stop()

    with st.status("🚀 正在生成高质量软文...", expanded=True) as gen_status:
        web_content = ""
        web_status = []
        if use_web:
            st.write("🌐 正在并行抓取全网资料（10 个来源）...")
            web_content, web_status = fetch_web_knowledge()
            ok_count = sum(1 for s in web_status if s["ok"])
            st.write(
                f"{'✅' if ok_count >= len(web_status) * 0.6 else '⚠️'} "
                f"网络抓取完成：{ok_count}/{len(web_status)} 个来源"
            )

        serp_context = ""
        if use_serp and keywords.strip():
            st.write("🔍 正在分析 Google Top 10 竞品...")
            primary_kw = keywords.strip().split(",")[0].strip()
            try:
                serp_data = analyze_serp(primary_kw)
                st.session_state["last_serp"] = serp_data
                serp_context = serp_to_prompt_context(serp_data)
                st.write(f"✅ SERP 分析完成：{len(serp_data.get('results', []))} 条竞品数据")
            except Exception as serp_err:
                st.write(f"⚠️ SERP 分析失败：{serp_err}")

        combined_web = web_content
        if serp_context:
            combined_web = web_content + "\n\n" + serp_context if web_content else serp_context

        st.write("🤖 AI 正在撰写文章（约 15-30 秒）...")
        try:
            client = get_client(api_key_input, base_url_input)
            result = generate_article(
                client=client,
                model=model_input.strip() if model_input else "gemini-2.5-flash",
                language=language,
                scenario_label=selected_scenario_label,
                audience_tag=selected_scenario.get("audience_tag", ""),
                selling_points_text=selling_points_text,
                style_name=selected_style_key,
                style_instruction=style_obj["instruction"],
                keywords=keywords,
                web_content=combined_web,
                geo_mode=geo_mode,
            )
            st.session_state["last_result"] = result
            st.session_state["last_language"] = language
            st.session_state["last_keywords"] = keywords
            st.session_state["last_sp_ids"] = selected_sp_ids
            st.session_state["last_scenario"] = selected_scenario
            st.session_state["last_geo_mode"] = geo_mode
            st.write("✅ 文章生成完成")

        except json.JSONDecodeError:
            st.error("❌ AI 返回格式异常，无法解析 JSON。请重试。")
            st.stop()
        except Exception as e:
            err = str(e)
            if "api_key" in err.lower() or "auth" in err.lower():
                st.error("❌ API Key 无效或已过期。")
            elif "model" in err.lower() or "not found" in err.lower():
                st.error(f"❌ 模型 `{model_input}` 不可用。请在侧边栏切换模型。")
            elif "rate" in err.lower():
                st.error("❌ 触发速率限制，请稍后重试。")
            else:
                st.error(f"❌ 生成失败：{err}")
            st.stop()

        if use_images:
            st.write("🖼️ 正在获取配图（Pixabay → Pexels → Placewise）...")
            scenario_terms = st.session_state["last_scenario"].get("pixabay_terms", [])
            ai_terms = result.get("image_search_terms", [])
            pixabay_images = fetch_images_for_article(
                pixabay_key=pixabay_key,
                pexels_key=pexels_key,
                scenario_terms=scenario_terms,
                ai_terms=ai_terms,
                per_query=2,
            )
            st.session_state["last_pixabay"] = pixabay_images
            sources = set(img.get("source", "") for img in pixabay_images)
            st.write(f"✅ 获取 {len(pixabay_images)} 张配图（来源: {', '.join(sources) if sources else 'N/A'}）")
        else:
            st.session_state["last_pixabay"] = []

        if "generation_history" not in st.session_state:
            st.session_state["generation_history"] = []
        st.session_state["generation_history"].insert(0, {
            "timestamp": datetime.now().strftime("%m/%d %H:%M"),
            "scenario": selected_scenario_label,
            "title": result.get("seo_title", ""),
            "result": dict(result),
            "language": language,
            "keywords": keywords,
            "pixabay_images": list(st.session_state.get("last_pixabay", [])),
        })
        if len(st.session_state["generation_history"]) > 20:
            st.session_state["generation_history"] = \
                st.session_state["generation_history"][:20]

        gen_status.update(label="✅ 生成完成！", state="complete")


# ══════════════════════════════════════════════════════════════════════════════
# 输出展示
# ══════════════════════════════════════════════════════════════════════════════
if "last_result" in st.session_state:
    result = st.session_state["last_result"]

    # ── Module A: SEO 元数据 ─────────────────────────────────────────────────
    st.markdown('<div class="output-card-title">📌 模块 A — SEO 元数据</div>',
                unsafe_allow_html=True)

    seo_title = result.get("seo_title", "（未生成）")
    meta_desc = result.get("meta_description", "（未生成）")
    slug = result.get("slug_suggestion", "") or generate_slug(seo_title)

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("**🏷️ SEO Title**")
        st.markdown(f'<div class="seo-title-box">{seo_title}</div>', unsafe_allow_html=True)
        st.caption(f"字符数：{len(seo_title)} / 建议 50-60")
    with col_a2:
        st.markdown("**📝 Meta Description**")
        st.markdown(f'<div class="seo-desc-box">{meta_desc}</div>', unsafe_allow_html=True)
        st.caption(f"字符数：{len(meta_desc)} / 建议 120-160")

    st.markdown(f"**🔗 URL Slug:** `/{slug}`")

    title_alts = result.get("title_alternatives", [])
    if title_alts:
        st.markdown("**🔀 A/B 备选标题**")
        for ti, alt_title in enumerate(title_alts):
            tcol_text, tcol_btn = st.columns([5, 1])
            with tcol_text:
                st.markdown(f"`{alt_title}` ({len(alt_title)} 字符)")
            with tcol_btn:
                if st.button("采用", key=f"use_alt_title_{ti}"):
                    st.session_state["last_result"]["seo_title"] = alt_title
                    st.rerun()

    with st.expander("📋 复制 SEO 元数据"):
        st.code(
            f"Title:\n{seo_title}\n\nMeta Description:\n{meta_desc}\n\nSlug:\n/{slug}",
            language="text",
        )

    st.divider()

    # ── Module B: 正文 ───────────────────────────────────────────────────────
    st.markdown('<div class="output-card-title">📄 模块 B — 正文内容</div>',
                unsafe_allow_html=True)
    article = result.get("article", "（未生成）")

    pixabay_images_for_insert = st.session_state.get("last_pixabay", [])

    if pixabay_images_for_insert:
        article_with_images = insert_images_into_article(
            article, pixabay_images_for_insert
        )
        _lines = article.split('\n')
        _h2_idx = [i for i, ln in enumerate(_lines) if ln.strip().startswith('## ')]
        if len(_h2_idx) >= 2:
            _img_positions = _h2_idx[1::2][:3]
        elif _h2_idx:
            _img_positions = [_h2_idx[0]]
        else:
            _img_positions = []
        _img_map: dict[int, dict] = {}
        for _pi, _pos in enumerate(_img_positions):
            if _pi < len(pixabay_images_for_insert):
                _img_map[_pos] = pixabay_images_for_insert[_pi]
        _chunk: list[str] = []
        for _li, _line in enumerate(_lines):
            _chunk.append(_line)
            if _li in _img_map:
                st.markdown('\n'.join(_chunk))
                _chunk = []
                _img = _img_map[_li]
                st.image(
                    _img['url'],
                    caption=f"📷 {_img['photographer']} via {_img.get('source', 'Pixabay')}",
                    use_container_width=True,
                )
        if _chunk:
            st.markdown('\n'.join(_chunk))
    else:
        article_with_images = article
        st.markdown(article)

    export_col1, export_col2, export_col3 = st.columns(3)
    with export_col1:
        st.download_button(
            "📥 导出 Markdown",
            data=f"# {seo_title}\n\n> {meta_desc}\n\n---\n\n{article_with_images}",
            file_name=f"{slug or 'mpchat-article'}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with export_col2:
        html_body = md_lib.markdown(
            article_with_images,
            extensions=["tables", "fenced_code"],
        )
        html_content = (
            "<!DOCTYPE html>\n"
            '<html lang="zh-CN"><head><meta charset="UTF-8">\n'
            f'<meta name="description" content="{meta_desc}">\n'
            f"<title>{seo_title}</title>\n"
            "<style>"
            "body{font-family:system-ui,sans-serif;max-width:800px;"
            "margin:0 auto;padding:40px 20px;line-height:1.8;color:#1a1a1a}"
            "h1{color:#00c853}"
            "h2{color:#0d2137;border-bottom:2px solid #00c85330;padding-bottom:8px}"
            "a{color:#00c853}"
            "img{max-width:100%;height:auto;border-radius:8px;margin:16px 0}"
            "table{border-collapse:collapse;width:100%}"
            "th,td{border:1px solid #ddd;padding:8px 12px}"
            "th{background:#f5f5f5}"
            "blockquote{border-left:4px solid #00c853;padding-left:16px;"
            "color:#555;margin:16px 0}"
            "code{background:#f0f0f0;padding:2px 6px;border-radius:4px}"
            "pre{background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:8px;"
            "overflow-x:auto}"
            "</style>\n</head><body>\n"
            f"{html_body}\n"
            "</body></html>"
        )
        st.download_button(
            "📥 导出 HTML",
            data=html_content,
            file_name=f"{slug or 'mpchat-article'}.html",
            mime="text/html",
            use_container_width=True,
        )
    with export_col3:
        full_export = (
            f"SEO Title: {seo_title}\n"
            f"Meta Description: {meta_desc}\n"
            f"Slug: /{slug}\n\n"
            f"{'='*60}\n\n{article}"
        )
        st.download_button(
            "📥 导出纯文本",
            data=full_export,
            file_name=f"{slug or 'mpchat-article'}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with st.expander("📋 复制 Markdown 源码"):
        st.code(article_with_images, language="markdown")

    st.divider()

    # ── Module C: 配图（多图库 + AI Prompt） ────────────────────────────────
    st.markdown('<div class="output-card-title">🎨 模块 C — 文章配图</div>',
                unsafe_allow_html=True)

    pixabay_images = st.session_state.get("last_pixabay", [])
    if pixabay_images:
        st.markdown(f"**📸 图库实图（{len(pixabay_images)} 张）**")
        img_cols = st.columns(min(len(pixabay_images), 4))
        for i, img in enumerate(pixabay_images):
            with img_cols[i % len(img_cols)]:
                st.image(img["url"], caption=img["alt_text"], use_container_width=True)
                source = img.get("source", "Pixabay")
                st.caption(f"📷 {img['photographer']} · [{source}]({img['page_url']})")
        st.divider()
    else:
        ai_search_terms = result.get("image_search_terms", [])
        st.info(
            f"📷 未获取到图片。\n\n"
            f"**AI 建议搜索词:** {', '.join(ai_search_terms) if ai_search_terms else '无'}\n\n"
            f"请确认：已开启「获取配图」开关"
        )

    image_prompts = result.get("image_prompts", [])
    if image_prompts:
        st.markdown("**🎨 AI 配图提示词**")
        prompt_cols = st.columns(min(len(image_prompts), 3))
        for i, item in enumerate(image_prompts):
            with prompt_cols[i % len(prompt_cols)]:
                scene = item.get("scene", f"场景 {i+1}")
                prompt = item.get("prompt", "")
                st.markdown(f"**🖼️ 场景 {i+1}：{scene}**")
                st.markdown(
                    f'<div class="image-prompt-block">'
                    f'<span class="image-prompt-label">Midjourney / DALL-E Prompt</span>'
                    f'{prompt}'
                    f'<div class="image-prompt-cn">📖 画面说明：{scene}</div>'
                    f'</div>', unsafe_allow_html=True)

        with st.expander("📋 复制全部 Image Prompts"):
            all_prompts = "\n\n".join(
                f"【场景 {i+1}：{it.get('scene','')}】\n{it.get('prompt','')}"
                for i, it in enumerate(image_prompts))
            st.code(all_prompts, language="text")

    if not pixabay_images and not image_prompts:
        st.info("暂无配图。")

    st.divider()

    # ── Module D: SEO / GEO 工具箱 ───────────────────────────────────────────
    st.markdown('<div class="output-card-title">🛠️ 模块 D — SEO / GEO 工具箱</div>',
                unsafe_allow_html=True)

    tab_schema, tab_links, tab_stats, tab_geo, tab_dual, tab_ai_detect = st.tabs(
        ["📋 Schema", "🔗 内部链接", "📊 SEO 评分",
         "🧠 GEO 评分", "⚡ 双优化", "🤖 AI 检测"]
    )

    with tab_schema:
        first_img_url = pixabay_images[0]["url"] if pixabay_images else ""
        schema_json = generate_schema(
            title=seo_title,
            description=meta_desc,
            image_url=first_img_url,
        )
        st.code(schema_json, language="json")
        st.caption("将此 JSON-LD 代码插入文章页面的 <head> 标签中")

        faq_pairs = result.get("faq_pairs", [])
        if faq_pairs:
            st.divider()
            st.markdown("**FAQPage Schema（GEO 加分项）**")
            faq_schema = generate_faq_schema(faq_pairs)
            st.code(faq_schema, language="json")
            st.caption("FAQ Schema 有助于在 AI 搜索引擎和 Google 精选摘要中展示")

    with tab_links:
        last_sp = st.session_state.get("last_sp_ids", [])
        links = generate_internal_links(last_sp)
        for lnk in links:
            st.markdown(f"- [{lnk['text']}]({lnk['url']})")
        ai_links = result.get("internal_links", [])
        if ai_links:
            st.markdown("**AI 建议的链接：**")
            for url in ai_links:
                st.markdown(f"- [{url}]({url})")

    with tab_stats:
        kw_for_stats = st.session_state.get("last_keywords", "")
        stats = reading_stats(article, kw_for_stats)

        score = stats["structure_score"]
        if score >= 80:
            score_color = "#00c853"
        elif score >= 50:
            score_color = "#fbbf24"
        else:
            score_color = "#f87171"

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("总字数", f"{stats['word_count']}")
        with m2:
            st.metric("阅读时间", f"{stats['reading_time_min']} 分钟")
        with m3:
            st.metric("H2 段落数", f"{stats['h2_count']}")
        with m4:
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<div class='score-ring' style='border:3px solid {score_color};color:{score_color};'>"
                f"{score}</div>"
                f"<div style='font-size:0.75rem;color:#6b7280;margin-top:4px;'>SEO 评分</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown(f"**CTA 检测：** {'✅ 包含 CTA' if stats['has_cta'] else '❌ 缺少 CTA'}")

        if stats["keyword_density"]:
            st.markdown("**关键词密度分析：**")
            for kw, info in stats["keyword_density"].items():
                st.markdown(
                    f"- `{kw}` — 出现 {info['count']} 次，密度 {info['density_pct']}%"
                )

        if score < 90:
            st.divider()
            st.markdown(f"**当前评分 {score}/100，建议优化到 90+ 以获得更好的 SEO 效果**")
            if st.button("🚀 一键 SEO 优化到 90+", use_container_width=True,
                         key="seo_optimize_btn"):
                issues = []
                if stats["h1_count"] < 1:
                    issues.append("缺少 H1 标题（用 # 开头）")
                if stats["h2_count"] < 2:
                    issues.append(f"H2 段落不足（当前 {stats['h2_count']} 个，建议至少 3 个）")
                if not stats["has_cta"]:
                    issues.append("缺少 CTA（如「立即下载」「免费注册」）")
                if stats["word_count"] < 600:
                    issues.append(f"字数偏少（当前 {stats['word_count']}，建议 800-1200）")
                if stats["keyword_density"]:
                    low_kw = [k for k, v in stats["keyword_density"].items() if v["count"] < 2]
                    if low_kw:
                        issues.append(f"关键词出现次数不足：{', '.join(low_kw)}")

                optimize_prompt = f"""请优化以下文章的 SEO 表现，目标评分 90-100 分。

【当前问题】
{chr(10).join(f'- {iss}' for iss in issues) if issues else '- 整体结构需要优化'}

【SEO 优化要求】
- 确保有 1 个 H1（#）和至少 3 个 H2（##）
- 自然增加关键词密度到 1-2%（关键词：{kw_for_stats}）
- 结尾必须有明确的 CTA（引导下载 MPChat 或申请 MP Card）
- 文章总长度 800-1200 字
- 每段不超过 150 字

【原文】
{article}

请直接输出优化后的完整文章（Markdown 格式），不要输出 JSON，不要解释修改内容。"""

                with st.spinner("🤖 正在 SEO 优化中..."):
                    try:
                        opt_client = get_client(api_key_input, base_url_input)
                        opt_response = opt_client.chat.completions.create(
                            model=model_input.strip() if model_input else "gemini-2.5-flash",
                            messages=[
                                {"role": "system", "content": "你是 SEO 优化专家，请直接输出优化后的 Markdown 文章。"},
                                {"role": "user", "content": optimize_prompt},
                            ],
                            temperature=0.6,
                            max_tokens=8000,
                        )
                        optimized = opt_response.choices[0].message.content.strip()
                        if optimized.startswith("```"):
                            opt_lines = optimized.split("\n")
                            opt_inner = "\n".join(opt_lines[1:])
                            if "```" in opt_inner:
                                optimized = opt_inner[:opt_inner.rfind("```")].strip()
                            else:
                                optimized = opt_inner.strip()

                        st.session_state["last_result"]["article"] = optimized
                        st.success("SEO 优化完成！文章已更新，切换其他 Tab 或滚动上方查看新内容。")
                    except Exception as e:
                        st.error(f"优化失败：{e}")

    # ── Tab: GEO 评分 ────────────────────────────────────────────────────────
    with tab_geo:
        faq_pairs_for_geo = result.get("faq_pairs", [])
        geo_result = geo_score(article, faq_pairs_for_geo)
        g_score = geo_result["score"]

        if g_score >= 80:
            g_color = "#00c853"
        elif g_score >= 50:
            g_color = "#fbbf24"
        else:
            g_color = "#f87171"

        gc1, gc2 = st.columns([1, 3])
        with gc1:
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<div class='score-ring' style='border:3px solid {g_color};color:{g_color};font-size:2rem;'>"
                f"{g_score}</div>"
                f"<div style='font-size:0.75rem;color:#6b7280;margin-top:4px;'>GEO 评分</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with gc2:
            details = geo_result["details"]
            st.markdown(f"""
| 指标 | 数值 |
|---|---|
| 开头段落长度 | {details['answer_first_len']} 字 |
| 问句 H2 占比 | {details['question_h2_ratio']}% |
| 数据引用数 | {details['citation_count']} 处 |
| 长段落数 | {details['long_paragraphs']} 个 |
| 实体提及数 | {details['entity_mentions']} 种 |
| FAQ 数量 | {details['faq_count']} 对 |
| 权威引用 | {details['authority_refs']} 处 |
""")

        if geo_result["issues"]:
            st.markdown("**需改进的问题：**")
            for iss in geo_result["issues"]:
                st.markdown(f"- {iss}")
        if geo_result["tips"]:
            st.markdown("**优化建议：**")
            for tip in geo_result["tips"]:
                st.markdown(f"- {tip}")

        if g_score < 90:
            st.divider()
            st.markdown(f"**当前 GEO 评分 {g_score}/100，建议优化到 90+ 以提升 AI 搜索可见性**")
            if st.button("🧠 一键 GEO 优化到 90+", use_container_width=True,
                         key="geo_optimize_btn"):
                geo_opt_prompt = build_geo_optimize_prompt(
                    article, geo_result,
                    keywords=st.session_state.get("last_keywords", "")
                )
                with st.spinner("🤖 正在 GEO 优化中..."):
                    try:
                        opt_client = get_client(api_key_input, base_url_input)
                        opt_response = opt_client.chat.completions.create(
                            model=model_input.strip() if model_input else "gemini-2.5-flash",
                            messages=[
                                {"role": "system", "content": "你是 GEO（Generative Engine Optimization）专家，专门优化内容以提升在 ChatGPT、Perplexity、Gemini 等 AI 搜索引擎中的可见性。请直接输出优化后的 Markdown 文章。"},
                                {"role": "user", "content": geo_opt_prompt},
                            ],
                            temperature=0.6,
                            max_tokens=8000,
                        )
                        optimized = opt_response.choices[0].message.content.strip()
                        if optimized.startswith("```"):
                            opt_lines = optimized.split("\n")
                            opt_inner = "\n".join(opt_lines[1:])
                            if "```" in opt_inner:
                                optimized = opt_inner[:opt_inner.rfind("```")].strip()
                            else:
                                optimized = opt_inner.strip()

                        st.session_state["last_result"]["article"] = optimized
                        st.success("GEO 优化完成！文章已更新，切换其他 Tab 或滚动上方查看新内容。")
                    except Exception as e:
                        st.error(f"GEO 优化失败：{e}")

    # ── Tab: SEO + GEO 双优化 ──────────────────────────────────────────────
    with tab_dual:
        st.markdown("**SEO + GEO 联合优化**")
        st.caption("同时将 SEO 和 GEO 评分优化到 90+，避免优化一项时拉低另一项")

        kw_dual = st.session_state.get("last_keywords", "")
        faq_dual = result.get("faq_pairs", [])
        stats_dual = reading_stats(article, kw_dual)
        geo_dual = geo_score(article, faq_dual)

        dc1, dc2 = st.columns(2)
        seo_s = stats_dual["structure_score"]
        geo_s = geo_dual["score"]
        seo_c = "#00c853" if seo_s >= 90 else ("#fbbf24" if seo_s >= 50 else "#f87171")
        geo_c = "#00c853" if geo_s >= 90 else ("#fbbf24" if geo_s >= 50 else "#f87171")

        with dc1:
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<div class='score-ring' style='border:3px solid {seo_c};color:{seo_c};font-size:1.8rem;'>"
                f"{seo_s}</div>"
                f"<div style='font-size:0.75rem;color:#6b7280;margin-top:4px;'>SEO 评分</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with dc2:
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<div class='score-ring' style='border:3px solid {geo_c};color:{geo_c};font-size:1.8rem;'>"
                f"{geo_s}</div>"
                f"<div style='font-size:0.75rem;color:#6b7280;margin-top:4px;'>GEO 评分</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        both_pass = seo_s >= 90 and geo_s >= 90
        if both_pass:
            st.success("SEO 和 GEO 评分均已达到 90+，无需优化！")
        else:
            shortfalls = []
            if seo_s < 90:
                shortfalls.append(f"SEO {seo_s} → 90+")
            if geo_s < 90:
                shortfalls.append(f"GEO {geo_s} → 90+")
            st.markdown(f"**目标：** {' & '.join(shortfalls)}")

            if st.button("⚡ 一键 SEO + GEO 双优化到 90+", use_container_width=True,
                         key="dual_optimize_btn"):
                dual_prompt = build_dual_optimize_prompt(
                    article, stats_dual, geo_dual, keywords=kw_dual,
                )
                with st.spinner("🤖 正在联合优化 SEO + GEO（约 30 秒）..."):
                    try:
                        dual_client = get_client(api_key_input, base_url_input)
                        dual_response = dual_client.chat.completions.create(
                            model=model_input.strip() if model_input else "gemini-2.5-flash",
                            messages=[
                                {"role": "system", "content": "你是同时精通 SEO 和 GEO（Generative Engine Optimization）的内容优化专家。你必须同时满足 SEO 和 GEO 两套评分标准，不能为了一项牺牲另一项。请直接输出优化后的 Markdown 文章。"},
                                {"role": "user", "content": dual_prompt},
                            ],
                            temperature=0.6,
                            max_tokens=10000,
                        )
                        optimized = dual_response.choices[0].message.content.strip()
                        if optimized.startswith("```"):
                            d_lines = optimized.split("\n")
                            d_inner = "\n".join(d_lines[1:])
                            if "```" in d_inner:
                                optimized = d_inner[:d_inner.rfind("```")].strip()
                            else:
                                optimized = d_inner.strip()

                        st.session_state["last_result"]["article"] = optimized
                        st.success(f"双优化完成！（优化前：SEO {seo_s} / GEO {geo_s}）文章已更新。")
                    except Exception as e:
                        st.error(f"双优化失败：{e}")

    # ── Tab: AI 检测 + 人性化 ────────────────────────────────────────────────
    with tab_ai_detect:
        st.markdown("**AI 内容检测 & 人性化改写**")
        st.caption("检测 AI 生成痕迹，一键人性化改写，或三合一优化（SEO + GEO + 人性化）")

        if st.button("🔍 检测 AI 痕迹", use_container_width=True, key="ai_detect_btn"):
            detect_prompt = f"""请分析以下文章，评估其被 AI 检测工具（如 GPTZero、Originality.ai）判定为 AI 生成内容的可能性。

请输出：
1. AI 检测评分（0-100，0=完全人类，100=明显 AI）
2. 检测到的 AI 痕迹列表
3. 具体哪些段落或表述最像 AI 生成

请用以下格式输出：
AI 评分：XX/100
AI 痕迹：
- xxx
- xxx
高风险段落：
- "xxx" — 原因：xxx

【文章】
{article}"""

            with st.spinner("🔍 正在检测 AI 痕迹..."):
                try:
                    det_client = get_client(api_key_input, base_url_input)
                    det_response = det_client.chat.completions.create(
                        model=model_input.strip() if model_input else "gemini-2.5-flash",
                        messages=[
                            {"role": "system", "content": "你是 AI 内容检测专家，擅长分析文本是否由 AI 生成。"},
                            {"role": "user", "content": detect_prompt},
                        ],
                        temperature=0.3,
                        max_tokens=2000,
                    )
                    detect_result = det_response.choices[0].message.content.strip()
                    st.session_state["ai_detect_result"] = detect_result
                except Exception as e:
                    st.error(f"检测失败：{e}")

        if st.session_state.get("ai_detect_result"):
            st.markdown(st.session_state["ai_detect_result"])
            st.divider()

        kw_human = st.session_state.get("last_keywords", "MPChat, 加密支付")

        col_hum, col_tri = st.columns(2)

        with col_hum:
            do_humanize = st.button("✍️ 人性化改写", use_container_width=True, key="humanize_btn")
        with col_tri:
            do_triple = st.button("🚀 三合一优化", use_container_width=True, key="triple_btn",
                                  help="同时优化 SEO + GEO + 降低 AI 检测率")

        if do_humanize:
            humanize_prompt = f"""请将以下文章进行人性化改写，目标：降低 AI 检测率至 30 以下。

⚠️ 核心约束：人性化的同时 必须保留 以下 SEO / GEO 结构元素（不可删除或弱化）：
1. H1 标题（#）和所有 H2 标题（##）的结构与关键词
2. 关键词自然分布：{kw_human}
3. 所有数据引用和统计数字（如「据...报告，...」格式）
4. FAQ 段落（## 常见问题）及其全部 Q&A 对
5. CTA 段落（引导下载 MPChat 或申请 MP Card）
6. 产品实体名称 MPChat / MP Card / MP Wallet / mp.net
7. 权威来源引用（Chainalysis、CoinDesk 等）

人性化改写技巧（在保留以上结构的前提下应用）：
- 口语化、个人化表达（如「说实话」「我自己的体验是」）
- 增加主观感受和具体细节
- 打破 AI 固定句式（避免「首先…其次…最后…」等模板）
- 变化句子长度（短句长句交替，偶尔用感叹句、反问句）
- 适当使用不完美表达（口语缩写、省略）
- 增加故事元素和场景描写

【原文】
{article}

请直接输出改写后的完整文章（Markdown 格式），保留所有 H1/H2/FAQ/CTA 结构。"""

            with st.spinner("✍️ 正在人性化改写中..."):
                try:
                    hum_client = get_client(api_key_input, base_url_input)
                    hum_response = hum_client.chat.completions.create(
                        model=model_input.strip() if model_input else "gemini-2.5-flash",
                        messages=[
                            {"role": "system", "content": "你是一位资深的人类内容编辑。改写时必须保留文章的 H1/H2 标题结构、FAQ 段落、CTA、数据引用和关键词分布，只改写行文风格使之更自然。"},
                            {"role": "user", "content": humanize_prompt},
                        ],
                        temperature=0.8,
                        max_tokens=8000,
                    )
                    humanized = hum_response.choices[0].message.content.strip()
                    if humanized.startswith("```"):
                        h_lines = humanized.split("\n")
                        h_inner = "\n".join(h_lines[1:])
                        if "```" in h_inner:
                            humanized = h_inner[:h_inner.rfind("```")].strip()
                        else:
                            humanized = h_inner.strip()

                    st.session_state["last_result"]["article"] = humanized
                    st.session_state["ai_detect_result"] = ""
                    st.success("人性化改写完成！文章已更新，切换其他 Tab 查看新评分。")
                except Exception as e:
                    st.error(f"人性化改写失败：{e}")

        if do_triple:
            from geo_tools import build_triple_optimize_prompt
            faq_tri = result.get("faq_pairs", [])
            geo_tri = geo_score(article, faq_tri)
            stats_tri = reading_stats(article, kw_human)
            triple_prompt = build_triple_optimize_prompt(
                article, stats_tri, geo_tri, keywords=kw_human
            )

            with st.spinner("🚀 三合一优化中（SEO + GEO + 人性化，约 40 秒）..."):
                try:
                    tri_client = get_client(api_key_input, base_url_input)
                    tri_response = tri_client.chat.completions.create(
                        model=model_input.strip() if model_input else "gemini-2.5-flash",
                        messages=[
                            {"role": "system", "content": "你是同时精通 SEO、GEO 和人性化写作的内容专家。你的目标是输出一篇 SEO ≥ 90、GEO ≥ 90、AI 检测率 ≤ 30 的文章。"},
                            {"role": "user", "content": triple_prompt},
                        ],
                        temperature=0.7,
                        max_tokens=10000,
                    )
                    tripled = tri_response.choices[0].message.content.strip()
                    if tripled.startswith("```"):
                        t_lines = tripled.split("\n")
                        t_inner = "\n".join(t_lines[1:])
                        if "```" in t_inner:
                            tripled = t_inner[:t_inner.rfind("```")].strip()
                        else:
                            tripled = t_inner.strip()

                    seo_before = stats_tri.get("structure_score", 0)
                    geo_before = geo_tri["score"]
                    st.session_state["last_result"]["article"] = tripled
                    st.session_state["ai_detect_result"] = ""
                    st.success(f"三合一优化完成！（优化前：SEO {seo_before} / GEO {geo_before}）文章已更新。")
                except Exception as e:
                    st.error(f"三合一优化失败：{e}")

    st.divider()

    # ── Module E: 多平台分发 ──────────────────────────────────────────────────
    st.markdown('<div class="output-card-title">📡 模块 E — 多平台分发</div>',
                unsafe_allow_html=True)

    dist_tabs = st.tabs([
        "🔗 Dev.to", "🔗 Hashnode", "📝 Medium", "💼 LinkedIn",
        "🐦 Twitter", "📖 知乎", "📱 微信公众号", "🔐 加密博客"
    ])

    slug = result.get("slug_suggestion", "")

    with dist_tabs[0]:
        st.markdown("**Dev.to — API 直发**")
        if devto_key:
            pub_draft = st.radio("发布模式", ["草稿", "直接发布"],
                                 index=0, key="devto_mode")
            if st.button("📤 发布到 Dev.to", key="pub_devto"):
                with st.spinner("正在发布..."):
                    res = publish_to_devto(
                        devto_key, seo_title, article,
                        tags=["crypto", "payment", "web3", "fintech"],
                        published=(pub_draft == "直接发布"),
                    )
                    if res["ok"]:
                        st.success(f"发布成功！{res['url']}")
                    else:
                        st.error(f"发布失败：{res['error']}")
        else:
            st.info("请在左侧「多平台分发」中配置 Dev.to API Key")

    with dist_tabs[1]:
        st.markdown("**Hashnode — API 直发**")
        if hashnode_token and hashnode_pub_id:
            if st.button("📤 发布到 Hashnode", key="pub_hashnode"):
                with st.spinner("正在发布..."):
                    res = publish_to_hashnode(
                        hashnode_token, hashnode_pub_id,
                        seo_title, article,
                        tags=["crypto", "payment", "web3"],
                        slug=slug,
                    )
                    if res["ok"]:
                        st.success(f"发布成功！{res['url']}")
                    else:
                        st.error(f"发布失败：{res['error']}")
        else:
            st.info("请在左侧「多平台分发」中配置 Hashnode Token 和 Publication ID")

    with dist_tabs[2]:
        st.markdown("**Medium — 格式化复制**")
        medium_text = format_for_medium(seo_title, article, meta_desc)
        st.text_area("Medium 格式（Markdown）", medium_text, height=300, key="medium_copy")
        st.caption("复制后在 Medium 新文章页面使用 Markdown 导入")

    with dist_tabs[3]:
        st.markdown("**LinkedIn — 格式化复制**")
        linkedin_text = format_for_linkedin(seo_title, article)
        st.text_area("LinkedIn 帖子", linkedin_text, height=300, key="linkedin_copy")
        st.caption(f"字符数：{len(linkedin_text)} / 3000")

    with dist_tabs[4]:
        st.markdown("**Twitter — 线程拆分**")
        thread = format_for_twitter_thread(seo_title, article)
        for i, tweet in enumerate(thread):
            st.text_area(f"Tweet {i+1}", tweet, height=80,
                         key=f"tweet_{i}", disabled=True)
        st.caption(f"共 {len(thread)} 条推文")

    with dist_tabs[5]:
        st.markdown("**知乎 — 格式化复制**")
        zhihu_text = format_for_zhihu(seo_title, article)
        st.text_area("知乎文章", zhihu_text, height=300, key="zhihu_copy")

    with dist_tabs[6]:
        st.markdown("**微信公众号 — 纯文本**")
        wechat_text = format_for_wechat(seo_title, article)
        st.text_area("公众号文章", wechat_text, height=300, key="wechat_copy")
        st.caption("已自动去除外链和 Markdown 格式")

    with dist_tabs[7]:
        st.markdown("**加密博客投稿 — Frontmatter 格式**")
        crypto_text = format_for_crypto_submission(
            seo_title, article, meta_desc, slug=slug,
        )
        st.text_area("投稿包", crypto_text, height=300, key="crypto_copy")
        st.caption("适用于 CoinTelegraph / Bitcoin Magazine / Decrypt 等投稿")

    st.divider()

    # ── SERP 分析结果 ─────────────────────────────────────────────────────────
    serp_data = st.session_state.get("last_serp")
    if serp_data and serp_data.get("results"):
        with st.expander("🔍 SERP 竞品分析结果", expanded=False):
            st.markdown(f"**关键词：** `{serp_data['keyword']}`")
            st.markdown(f"**分析竞品数：** {len(serp_data['results'])}")
            for i, sr in enumerate(serp_data["results"][:10], 1):
                st.markdown(f"{i}. [{sr['title']}]({sr['url']})")
                if sr.get("snippet"):
                    st.caption(sr["snippet"][:150])
            if serp_data.get("recommendation"):
                st.markdown("**策略建议：**")
                st.markdown(serp_data["recommendation"])

    with st.expander("🔧 查看完整 JSON（调试用）"):
        st.json(result)

else:
    st.markdown("""
<div style="text-align:center; padding:60px 20px; color:#4b5563;
    background:#0d1117; border:1px dashed #1f2937; border-radius:12px;">
    <div style="font-size:3rem; margin-bottom:16px;">🌿</div>
    <div style="font-size:1.1rem; color:#6b7280; margin-bottom:8px;">
        在左侧选择写作场景和参数，点击「🚀 生成高质量软文」开始创作
    </div>
    <div style="font-size:0.85rem; color:#374151;">
        37+ 细分场景 · 16 种语言 · GEO + SEO 双优化 · 多平台分发 · 批量生成 · A/B 标题
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 历史记录
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.get("generation_history"):
    st.divider()
    history = st.session_state["generation_history"]
    with st.expander(f"📜 生成历史（{len(history)} 篇）", expanded=False):
        for hi, hitem in enumerate(history):
            hcol_info, hcol_btn = st.columns([5, 1])
            with hcol_info:
                st.markdown(
                    f"**{hitem['title'][:50]}** · "
                    f"{hitem['scenario']} · "
                    f"{hitem['timestamp']}"
                )
            with hcol_btn:
                if st.button("加载", key=f"load_history_{hi}"):
                    st.session_state["last_result"] = hitem["result"]
                    st.session_state["last_pixabay"] = hitem.get(
                        "pixabay_images", []
                    )
                    st.session_state["last_keywords"] = hitem.get("keywords", "")
                    st.session_state["last_language"] = hitem.get("language", "中文")
                    st.rerun()
        if len(history) > 1:
            if st.button("🗑️ 清空历史", key="clear_history"):
                st.session_state["generation_history"] = []
                st.rerun()
