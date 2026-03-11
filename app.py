"""
MPChat 智能软文生成器 v3.0
32+ 细分场景 · 25+ 卖点 · 7 种文风 · Pixabay 实图 · SEO 工具箱
"""

import os
import json
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

from scenarios import (
    SCENARIO_CATEGORIES,
    SELLING_POINT_GROUPS,
    SP_ID_TO_LABEL,
    ARTICLE_STYLES,
    KEYWORD_PRESETS,
)
from pixabay_client import fetch_images_for_article
from seo_tools import (
    generate_slug,
    generate_schema,
    generate_internal_links,
    reading_stats,
)

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


def build_system_prompt(language: str, style_instruction: str,
                        scenario_label: str, web_content: str = "") -> str:
    lang_instruction = (
        "请使用中文（简体）输出所有内容。" if language == "中文 (Chinese)"
        else "Please output ALL content in English. Do not use Chinese anywhere in the article body."
    )
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
  "article": "完整文章正文（Markdown 格式，含 H1/H2/CTA）",
  "image_prompts": [
    {{
      "scene": "场景描述（中文）",
      "prompt": "英文 Midjourney/DALL-E 提示词（详细、专业、含风格/光线/构图）"
    }}
  ],
  "image_search_terms": ["英文Pixabay搜索词1", "英文搜索词2", "英文搜索词3"]
}}

【Image Prompt 规范】
- 必须是纯英文
- 必须包含：主体描述 + 环境背景 + 光影效果 + 艺术风格 + 质量标签
- 生成 2-3 个不同场景的 Prompt
- 禁止出现品牌 Logo 或真实人脸描写

【image_search_terms 规范】
- 提供 3-5 个英文关键词，用于在 Pixabay 搜索配图
- 关键词要具体、视觉化（如 "digital payment smartphone" 而非 "crypto"）
"""


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


def generate_article(client, model, language, scenario_label, audience_tag,
                     selling_points_text, style_name, style_instruction,
                     keywords, web_content=""):
    system_prompt = build_system_prompt(language, style_instruction,
                                        scenario_label, web_content)
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
            max_tokens=4000,
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
            max_tokens=4000,
        )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        inner = "\n".join(lines[1:])
        if "```" in inner:
            raw = inner[:inner.rfind("```")].strip()
        else:
            raw = inner.strip()

    import re
    if not raw.startswith("{"):
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            raw = match.group(0)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raw_fixed = re.sub(r',\s*}', '}', raw)
        raw_fixed = re.sub(r',\s*]', ']', raw_fixed)
        try:
            return json.loads(raw_fixed)
        except json.JSONDecodeError:
            return {
                "seo_title": "MPChat — Live with Crypto",
                "meta_description": "AI 生成内容解析失败，请重试。",
                "slug_suggestion": "mpchat-article",
                "article": raw,
                "image_prompts": [],
                "image_search_terms": ["crypto payment", "digital finance"],
            }


# ══════════════════════════════════════════════════════════════════════════════
# Streamlit 页面配置 + 全局样式
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="MPChat 智能软文生成器 v3.0",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root { --mp-green: #00c853; --mp-dark: #0a1628; --mp-card: #111827; }
.mp-banner {
    background: linear-gradient(135deg, #0a1628 0%, #0d2137 50%, #0a2e1a 100%);
    border: 1px solid #00c85330; border-radius: 12px;
    padding: 24px 32px; margin-bottom: 24px;
    display: flex; align-items: center; gap: 16px;
}
.mp-banner h1 { color: #fff; font-size: 1.8rem; font-weight: 700; margin: 0; }
.mp-banner p  { color: #a0aec0; font-size: 0.9rem; margin: 4px 0 0 0; }
.mp-badge {
    background: #00c85320; border: 1px solid #00c853; color: #00c853;
    border-radius: 20px; padding: 3px 12px; font-size: 0.75rem;
    font-weight: 600; display: inline-block; margin-top: 6px;
}
.output-card-title {
    color: #00c853; font-size: 0.85rem; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase;
    margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
}
.seo-title-box {
    background: #00c85310; border-left: 3px solid #00c853;
    border-radius: 0 8px 8px 0; padding: 12px 16px;
    color: #e2e8f0; font-size: 1.05rem; font-weight: 600; margin-bottom: 8px;
}
.seo-desc-box {
    background: #1e293b; border-radius: 8px; padding: 10px 14px;
    color: #94a3b8; font-size: 0.88rem; line-height: 1.6;
}
.image-prompt-block {
    background: #0f172a; border: 1px solid #1e3a5f; border-radius: 8px;
    padding: 14px 16px; margin-bottom: 10px;
    font-family: 'Courier New', monospace; font-size: 0.8rem;
    color: #7dd3fc; line-height: 1.7;
}
.image-prompt-label { color: #38bdf8; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; display: block; }
.image-prompt-cn { color: #64748b; font-size: 0.78rem; margin-top: 6px; padding-top: 6px; border-top: 1px solid #1e293b; }
.kw-badge {
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-size: 0.7rem; font-weight: 600; margin-left: 4px;
}
.kw-low  { background: #065f4620; color: #34d399; border: 1px solid #34d39940; }
.kw-med  { background: #92400e20; color: #fbbf24; border: 1px solid #fbbf2440; }
.kw-high { background: #7f1d1d20; color: #f87171; border: 1px solid #f8717140; }
.score-ring {
    display: inline-flex; align-items: center; justify-content: center;
    width: 56px; height: 56px; border-radius: 50%;
    font-size: 1.2rem; font-weight: 800;
}
[data-testid="stSidebar"] { background: #0d1117; }
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #00c853; font-size: 0.8rem; letter-spacing: 0.1em; text-transform: uppercase;
}
.stButton > button {
    background: linear-gradient(135deg, #00c853, #00a844);
    color: white; font-weight: 700; font-size: 1rem; border: none;
    border-radius: 10px; padding: 14px 0; width: 100%; transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #00e064, #00c853);
    transform: translateY(-1px); box-shadow: 0 4px 20px #00c85340;
}
hr { border-color: #1f2937; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Banner
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="mp-banner">
  <div><div style="font-size:2.2rem;">🌿</div></div>
  <div>
    <h1>MPChat 智能软文生成器</h1>
    <p>32+ 场景 · 25+ 卖点 · 7 种文风 · Pixabay 实图 · SEO 工具箱</p>
    <span class="mp-badge">v3.0 — Live with Crypto</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 侧边栏
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── 🔑 AI 服务商 ─────────────────────────────────────────────────────────
    st.markdown("### 🔑 AI 服务商配置")
    provider_name = st.selectbox(
        "选择 AI 服务商", options=list(PROVIDERS.keys()), index=0,
        help="选择后会自动填充 Base URL 和推荐模型",
    )
    provider = PROVIDERS[provider_name]

    env_key = os.getenv("OPENAI_API_KEY", "")
    api_key_input = st.text_input(
        "API Key", value=env_key, type="password",
        placeholder=provider["key_prefix"] or "输入 API Key",
    )
    if provider["get_key_url"]:
        st.caption(f"🔗 [获取 Key → {provider_name.split('（')[0].strip()}]({provider['get_key_url']})")

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

    # ── 🌐 语言 ──────────────────────────────────────────────────────────────
    st.markdown("### 🌐 语言")
    language = st.radio("输出语言", ["中文 (Chinese)", "英文 (English)"],
                        index=0, label_visibility="collapsed")

    st.divider()

    # ── 🎯 场景选择（二级） ──────────────────────────────────────────────────
    st.markdown("### 🎯 写作场景")
    category_names = list(SCENARIO_CATEGORIES.keys())
    selected_category = st.selectbox("场景分类", category_names, index=0,
                                     label_visibility="collapsed")
    scenarios_in_cat = SCENARIO_CATEGORIES[selected_category]
    scenario_labels = [s["label"] for s in scenarios_in_cat]
    selected_scenario_label = st.radio("具体场景", scenario_labels, index=0,
                                       label_visibility="collapsed")
    selected_scenario = next(
        s for s in scenarios_in_cat if s["label"] == selected_scenario_label
    )

    st.divider()

    # ── 💎 卖点（5 组展开） ──────────────────────────────────────────────────
    st.markdown("### 💎 主打卖点（可多选）")

    auto_sp = set(selected_scenario.get("selling_points", []))

    if "sp_overrides" not in st.session_state:
        st.session_state["sp_overrides"] = {}

    selected_sp_ids: list[str] = []
    for group_name, items in SELLING_POINT_GROUPS.items():
        with st.expander(group_name, expanded=False):
            for sp_id, sp_label in items.items():
                default_val = sp_id in auto_sp
                override_key = f"sp_{sp_id}"
                checked = st.checkbox(
                    sp_label, value=default_val, key=override_key,
                )
                if checked:
                    selected_sp_ids.append(sp_id)

    selling_points_text = "、".join(
        SP_ID_TO_LABEL.get(sid, sid) for sid in selected_sp_ids
    ) if selected_sp_ids else "MPChat 全功能"

    st.divider()

    # ── ✍️ 文风（7 种） ──────────────────────────────────────────────────────
    st.markdown("### ✍️ 文章文风")
    style_hint = selected_scenario.get("style_hint", "pain_story")
    style_keys = list(ARTICLE_STYLES.keys())
    hint_index = 0
    for i, k in enumerate(style_keys):
        if ARTICLE_STYLES[k]["id"] == style_hint:
            hint_index = i
            break
    selected_style_key = st.radio(
        "文风",
        style_keys,
        index=hint_index,
        label_visibility="collapsed",
        format_func=lambda k: f"{k} — {ARTICLE_STYLES[k]['desc']}",
    )
    style_obj = ARTICLE_STYLES[selected_style_key]

    st.divider()

    # ── 🔍 SEO 关键词 ────────────────────────────────────────────────────────
    st.markdown("### 🔍 SEO 关键词")
    st.caption("点击预设快速填充，或手动编辑")

    preset_cols = st.columns(3)
    for i, preset in enumerate(KEYWORD_PRESETS):
        diff_cls = {"low": "kw-low", "medium": "kw-med", "high": "kw-high"}[preset["difficulty"]]
        diff_label = {"low": "易", "medium": "中", "high": "难"}[preset["difficulty"]]
        col = preset_cols[i % 3]
        with col:
            if st.button(
                f"{preset['label']}",
                key=f"kw_preset_{i}",
                use_container_width=True,
            ):
                st.session_state["keywords_val"] = preset["keywords"]

    scenario_kw = selected_scenario.get("keywords", "")
    default_kw = st.session_state.get("keywords_val", scenario_kw)

    keywords = st.text_area(
        "关键词（3-5个）",
        value=default_kw,
        height=80,
        label_visibility="collapsed",
        help="将被自然植入文章正文，提升 SEO 表现",
    )

    st.divider()

    # ── 🖼️ Pixabay 配图 ──────────────────────────────────────────────────────
    st.markdown("### 🖼️ Pixabay 配图")
    use_pixabay = st.toggle("获取 Pixabay 实际图片", value=True,
                            help="免费图库，无需署名，100 次/分钟")
    pixabay_key = ""
    if use_pixabay:
        pixabay_key = st.text_input(
            "Pixabay API Key",
            value=os.getenv("PIXABAY_API_KEY", "46561407-37c46214d0e52dffc32a430eb3"),
            type="password",
            placeholder="从 pixabay.com/api/docs 获取",
        )
        if not pixabay_key:
            st.caption("⚠️ 未填写 Key，将仅显示 AI 提示词")

    st.divider()

    # ── 🌍 网络知识库 ────────────────────────────────────────────────────────
    st.markdown("### 🌍 网络知识库")
    use_web = st.toggle("抓取全网 MPChat 资料", value=True,
                        help="官网 + Medium + Twitter + Google + 百度（点击生成时抓取，缓存 2 小时）")
    if use_web:
        st.caption("✅ 已开启 · 点击「生成」时自动并行抓取 10 个来源")

    st.divider()
    st.markdown(
        "<div style='color:#4b5563;font-size:0.75rem;text-align:center;'>"
        "MPChat 智能软文生成器 v3.0<br/>Live with Crypto 🌿</div>",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# 主区域 — 生成按钮
# ══════════════════════════════════════════════════════════════════════════════
col_info, col_btn = st.columns([3, 1])
with col_info:
    sp_summary = ", ".join(
        SP_ID_TO_LABEL.get(sid, sid).split("（")[0]
        for sid in selected_sp_ids[:4]
    ) or "（请选择卖点）"
    if len(selected_sp_ids) > 4:
        sp_summary += f" +{len(selected_sp_ids) - 4}"
    st.markdown(
        f"**当前配置** · {language} · {selected_scenario_label} "
        f"· {style_obj['id']} · 卖点: {sp_summary}",
        help="在左侧边栏调整参数",
    )
with col_btn:
    generate_btn = st.button("🚀 生成高质量软文", use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 生成逻辑
# ══════════════════════════════════════════════════════════════════════════════
if generate_btn:
    if not api_key_input.strip():
        st.error("❌ 请在左侧填写 API Key。")
        st.stop()
    if not selected_sp_ids:
        st.warning("⚠️ 请至少选择一个主打卖点。")
        st.stop()

    web_content = ""
    web_status = []
    if use_web:
        with st.spinner("🌐 正在并行抓取全网资料（约 3-5 秒）..."):
            web_content, web_status = fetch_web_knowledge()
        ok_count = sum(1 for s in web_status if s["ok"])
        total = len(web_status)
        color = "#00c853" if ok_count >= total * 0.6 else "#f59e0b"
        st.markdown(
            f"<div style='font-size:0.8rem;color:{color};'>"
            f"{'✅' if ok_count >= total * 0.6 else '⚠️'} "
            f"网络抓取完成：成功 {ok_count} / {total} 个来源</div>",
            unsafe_allow_html=True,
        )

    with st.spinner("🤖 AI 正在撰写中，请稍候（约 15-30 秒）..."):
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
                web_content=web_content,
            )
            st.session_state["last_result"] = result
            st.session_state["last_language"] = language
            st.session_state["last_keywords"] = keywords
            st.session_state["last_sp_ids"] = selected_sp_ids
            st.session_state["last_scenario"] = selected_scenario

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

    st.success("✅ 生成完成！")

    if use_pixabay and pixabay_key:
        with st.spinner("🖼️ 正在从 Pixabay 获取配图..."):
            scenario_terms = st.session_state["last_scenario"].get("pixabay_terms", [])
            ai_terms = result.get("image_search_terms", [])
            pixabay_images = fetch_images_for_article(
                pixabay_key,
                scenario_terms=scenario_terms,
                ai_terms=ai_terms,
                per_query=2,
            )
            st.session_state["last_pixabay"] = pixabay_images
    else:
        st.session_state["last_pixabay"] = []


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
    st.markdown(article)
    with st.expander("📋 复制 Markdown 源码"):
        st.code(article, language="markdown")

    st.divider()

    # ── Module C: 配图（Pixabay 实图 + AI Prompt） ───────────────────────────
    st.markdown('<div class="output-card-title">🎨 模块 C — 文章配图</div>',
                unsafe_allow_html=True)

    pixabay_images = st.session_state.get("last_pixabay", [])
    if pixabay_images:
        st.markdown("**📸 Pixabay 实际图片**")
        img_cols = st.columns(min(len(pixabay_images), 4))
        for i, img in enumerate(pixabay_images):
            with img_cols[i % len(img_cols)]:
                st.image(img["preview_url"], caption=img["alt_text"], use_container_width=True)
                st.caption(f"📷 {img['photographer']} · [Pixabay]({img['page_url']})")
        st.divider()

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

    # ── Module D: SEO 工具箱 ─────────────────────────────────────────────────
    st.markdown('<div class="output-card-title">🛠️ 模块 D — SEO 工具箱</div>',
                unsafe_allow_html=True)

    tab_schema, tab_links, tab_stats = st.tabs(
        ["📋 Schema JSON-LD", "🔗 内部链接", "📊 阅读统计"]
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
                bar_pct = min(info["density_pct"] * 20, 100)
                st.markdown(
                    f"- `{kw}` — 出现 {info['count']} 次，密度 {info['density_pct']}%"
                )

    st.divider()
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
        32+ 细分场景 · 7 种文风 · Pixabay 实图 · SEO 工具箱
    </div>
</div>
""", unsafe_allow_html=True)
