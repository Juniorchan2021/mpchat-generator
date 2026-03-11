"""
MPChat 智能软文生成器 v2.0
基于 MPChat 产品知识库 + 全网实时资料，自动生成 SEO 优化软文 + AI 配图 Prompt
"""

import os
import json
import time
import xml.etree.ElementTree as ET
import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# ── 环境变量 ──────────────────────────────────────────────────────────────────
load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# 🔧  AI 服务商预设配置
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
# 🌍  网络资料源配置
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

# ── 页面配置 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MPChat 智能软文生成器",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 全局样式 ──────────────────────────────────────────────────────────────────
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
# 📚  知识库加载
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
# 🌐  网络抓取引擎
# ══════════════════════════════════════════════════════════════════════════════
def _fetch_html(url: str, max_chars: int = 3000) -> str:
    """抓取普通网页，清洗后返回正文。"""
    try:
        r = requests.get(url, headers=HTTP_HEADERS, timeout=12,
                         allow_redirects=True)
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
    """通过 RSS Feed 抓取 Medium 博客文章摘要。"""
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
    """抓取搜索引擎结果页。"""
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
    """尝试通过 Nitter 镜像抓取 MPChat 推文。"""
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


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_web_knowledge() -> tuple[str, list[dict]]:
    """
    抓取全网 MPChat 资料，返回 (合并文本, 状态列表)。
    """
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

    results = []
    all_text_parts = []

    for label, fn in tasks:
        t0 = time.time()
        text = fn()
        elapsed = round(time.time() - t0, 1)
        ok = not text.startswith("[抓取失败")
        results.append({"label": label, "ok": ok, "elapsed": elapsed})
        if ok and len(text.strip()) > 50:
            all_text_parts.append(f"### 来源：{label}\n{text}")

    combined = "\n\n---\n\n".join(all_text_parts)
    return combined, results


# ══════════════════════════════════════════════════════════════════════════════
# 🤖  LLM 调用
# ══════════════════════════════════════════════════════════════════════════════
def get_client(api_key: str, base_url: str) -> OpenAI:
    kwargs = {"api_key": api_key}
    if base_url.strip():
        kwargs["base_url"] = base_url.strip()
    return OpenAI(**kwargs)


def build_system_prompt(language: str, web_content: str = "") -> str:
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

【你的核心职责】
基于用户提供的参数，创作一篇兼顾 SEO 优化和用户体验的高质量推广软文，并产出专业的 AI 绘画提示词。

【SEO 写作规范】
- 文章必须包含 H1（主标题，用 # 表示）、H2（副标题，用 ## 表示）、H3（可选，用 ### 表示）
- 自然植入用户指定的 SEO 关键词，不堆砌，保持阅读流畅
- 每段不超过 150 字，适合移动端阅读
- 文章总长度：800-1200 字（中文）/ 600-900 词（英文）
- 结尾必须有清晰有力的 CTA（Call to Action），引导用户下载 MPChat 或申请 MP Card

【内容质量要求】
- 痛点故事型：用第一/第二人称讲述真实场景，先痛后爽，情感共鸣
- 干货教程型：步骤清晰，有数据支撑，评测客观，种草自然
- 行业分析型：宏观视野，数据引用，专业术语适度，体现权威性

【输出格式要求（严格遵守 JSON 格式）】
请以合法的 JSON 格式输出，结构如下：
{{
  "seo_title": "文章 SEO 标题（50-60 字符，中文/英文，含核心关键词）",
  "meta_description": "元描述（120-160 字符，中文/英文，总结文章价值并含关键词）",
  "article": "完整文章正文（Markdown 格式，含 H1/H2/CTA）",
  "image_prompts": [
    {{
      "scene": "场景描述（中文）",
      "prompt": "英文 Midjourney/DALL-E 提示词（详细、专业、含风格/光线/构图）"
    }}
  ]
}}

【Image Prompt 规范】
- 必须是纯英文
- 必须包含：主体描述 + 环境背景 + 光影效果 + 艺术风格 + 质量标签
- 格式参考：High quality, 8k resolution, cinematic lighting, [主体], [环境], [氛围], photorealistic, shot on Sony A7R V, --ar 16:9
- 禁止出现品牌 Logo 或真实人脸描写
- 生成 2-3 个不同场景的 Prompt
"""


def build_user_prompt(language, audience, selling_points, style, keywords):
    sp_str = "、".join(selling_points) if selling_points else "MPChat 全功能"
    kw_str = keywords.strip() if keywords.strip() else "MPChat, 加密支付, 稳定币"
    return f"""请根据以下参数，生成一篇完整的 MPChat 推广软文和配套 AI 绘画提示词。

【生成参数】
- 输出语言：{language}
- 目标受众：{audience}
- 主打卖点：{sp_str}
- 文章文风：{style}
- SEO 核心关键词：{kw_str}

请严格按照系统提示中规定的 JSON 格式输出，确保 JSON 合法可解析。
"""


def generate_article(client, model, language, audience, selling_points,
                     style, keywords, web_content=""):
    system_prompt = build_system_prompt(language, web_content)
    user_prompt = build_user_prompt(language, audience, selling_points, style, keywords)

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
    return json.loads(raw)


# ══════════════════════════════════════════════════════════════════════════════
# 🎨  UI — 顶部 Banner
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="mp-banner">
  <div><div style="font-size:2.2rem;">🌿</div></div>
  <div>
    <h1>MPChat 智能软文生成器</h1>
    <p>产品知识库 + 全网实时抓取 · SEO 优化 · 中英双语 · AI 配图 Prompt</p>
    <span class="mp-badge">Live with Crypto</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 📋  UI — 侧边栏
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── 🔑 API 配置 ───────────────────────────────────────────────────────────
    st.markdown("### 🔑 AI 服务商配置")

    provider_name = st.selectbox(
        "选择 AI 服务商",
        options=list(PROVIDERS.keys()),
        index=0,
        help="选择后会自动填充 Base URL 和推荐模型",
    )
    provider = PROVIDERS[provider_name]

    # API Key
    env_key = os.getenv("OPENAI_API_KEY", "")
    api_key_input = st.text_input(
        "API Key",
        value=env_key,
        type="password",
        placeholder=provider["key_prefix"] or "输入 API Key",
    )
    if provider["get_key_url"]:
        st.caption(f"🔗 [获取 Key → {provider_name.split('（')[0].strip()}]({provider['get_key_url']})")

    # Base URL（自动填充，可手动覆盖）
    env_url = os.getenv("OPENAI_BASE_URL", "")
    default_url = env_url if env_url else provider["base_url"]
    base_url_input = st.text_input(
        "Base URL",
        value=default_url,
        help="已根据服务商自动填充，一般无需修改",
    )

    # 模型选择
    env_model = os.getenv("OPENAI_MODEL", "")
    if provider["models"]:
        model_input = st.selectbox(
            "模型",
            options=provider["models"],
            index=0,
            help="推荐使用列表中的第一个模型",
        )
    else:
        model_input = st.text_input(
            "模型名称",
            value=env_model or "",
            placeholder="手动输入模型名",
        )

    st.divider()

    # ── 🌐 语言 ───────────────────────────────────────────────────────────────
    st.markdown("### 🌐 语言")
    language = st.radio("输出语言", ["中文 (Chinese)", "英文 (English)"],
                        index=0, label_visibility="collapsed")

    st.divider()

    # ── 🎯 受众 ───────────────────────────────────────────────────────────────
    st.markdown("### 🎯 目标受众")
    audience = st.radio("目标受众", [
        "数字游民与出海创业者", "跨境务工与留学生",
        "Web3 极客与加密投资者", "开发者与社群主",
    ], index=0, label_visibility="collapsed")

    st.divider()

    # ── 💎 卖点 ───────────────────────────────────────────────────────────────
    st.markdown("### 💎 主打卖点（可多选）")
    sp_mp_card   = st.checkbox("💳 MP Card（全球消费）", value=True)
    sp_mp_chat   = st.checkbox("💬 MP Chat（加密社交与红包）", value=True)
    sp_mp_wallet = st.checkbox("🏦 MP Wallet（安全托管与理财）", value=False)
    sp_dev       = st.checkbox("⚙️ 开发者平台（MiniApp 生态）", value=False)

    selling_points = []
    if sp_mp_card:   selling_points.append("MP Card（全球消费，Visa/Mastercard网络，加密货币秒转法币）")
    if sp_mp_chat:   selling_points.append("MP Chat（端到端加密社交，加密红包，P2P即时转账）")
    if sp_mp_wallet: selling_points.append("MP Wallet（机构级合规托管，RWA理财，DEX交易）")
    if sp_dev:       selling_points.append("开发者平台（MiniApp生态，API/SDK，Bot框架，PSP能力）")

    st.divider()

    # ── ✍️ 文风 ───────────────────────────────────────────────────────────────
    st.markdown("### ✍️ 文章文风")
    style_map = {
        "🔥 痛点故事型（引发共鸣）": "痛点故事型",
        "📚 干货教程型（评测种草）": "干货教程型",
        "📊 行业分析型（宏观专业）": "行业分析型",
    }
    style_label = st.radio("文风", list(style_map.keys()), index=0,
                           label_visibility="collapsed")
    style = style_map[style_label]

    st.divider()

    # ── 🔍 关键词 ─────────────────────────────────────────────────────────────
    st.markdown("### 🔍 SEO 核心关键词")
    keywords = st.text_area("关键词（3-5个）",
                            placeholder="加密信用卡, USDT支付, 跨境汇款, 数字游民",
                            height=80, label_visibility="collapsed",
                            help="将被自然植入文章正文，提升 SEO 表现")

    st.divider()

    # ── 🌍 网络知识库 ─────────────────────────────────────────────────────────
    st.markdown("### 🌍 网络知识库")
    use_web = st.toggle("抓取全网 MPChat 资料", value=True,
                        help="官网 + Medium + Twitter + Google + 百度（缓存 1 小时）")
    if use_web:
        with st.spinner("🌐 正在抓取全网资料..."):
            web_content, web_status = fetch_web_knowledge()
        ok_count = sum(1 for s in web_status if s["ok"])
        total = len(web_status)
        color = "#00c853" if ok_count >= total * 0.6 else "#f59e0b"
        st.markdown(
            f"<div style='font-size:0.8rem;color:{color};'>"
            f"{'✅' if ok_count >= total * 0.6 else '⚠️'} "
            f"成功 {ok_count} / {total} 个来源</div>",
            unsafe_allow_html=True,
        )
        with st.expander(f"查看抓取详情（{ok_count}/{total}）"):
            for s in web_status:
                icon = "✅" if s["ok"] else "❌"
                st.markdown(
                    f"<div style='font-size:0.73rem;color:#9ca3af;'>"
                    f"{icon} {s['label']} ({s['elapsed']}s)</div>",
                    unsafe_allow_html=True,
                )
    else:
        web_content = ""

    st.divider()
    st.markdown(
        "<div style='color:#4b5563;font-size:0.75rem;text-align:center;'>"
        "MPChat 智能软文生成器 v2.0<br/>Live with Crypto 🌿</div>",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# 🎛️  UI — 主区域
# ══════════════════════════════════════════════════════════════════════════════
col_info, col_btn = st.columns([3, 1])
with col_info:
    active_sp = selling_points or ["（请至少选择一个卖点）"]
    st.markdown(
        f"**当前配置** · {language} · {audience} · {style} "
        f"· 卖点: {', '.join([s.split('（')[0] for s in active_sp])}",
        help="在左侧边栏调整参数",
    )
with col_btn:
    generate_btn = st.button("🚀 生成高质量软文", use_container_width=True)

st.divider()

# ── 生成逻辑 ──────────────────────────────────────────────────────────────────
if generate_btn:
    if not api_key_input.strip():
        st.error("❌ 请在左侧填写 API Key。")
        st.stop()
    if not selling_points:
        st.warning("⚠️ 请至少选择一个主打卖点。")
        st.stop()

    with st.spinner("🤖 AI 正在撰写中，请稍候（约 15-30 秒）..."):
        try:
            client = get_client(api_key_input, base_url_input)
            result = generate_article(
                client=client,
                model=model_input.strip() if model_input else "gemini-2.5-flash",
                language=language,
                audience=audience,
                selling_points=selling_points,
                style=style,
                keywords=keywords,
                web_content=web_content if use_web else "",
            )
            st.session_state["last_result"] = result
            st.session_state["last_language"] = language

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

# ── 输出展示 ──────────────────────────────────────────────────────────────────
if "last_result" in st.session_state:
    result = st.session_state["last_result"]

    st.markdown('<div class="output-card-title">📌 模块 A — SEO 元数据</div>',
                unsafe_allow_html=True)

    seo_title = result.get("seo_title", "（未生成）")
    meta_desc = result.get("meta_description", "（未生成）")

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("**🏷️ SEO Title**")
        st.markdown(f'<div class="seo-title-box">{seo_title}</div>', unsafe_allow_html=True)
        st.caption(f"字符数：{len(seo_title)} / 建议 50-60")
    with col_a2:
        st.markdown("**📝 Meta Description**")
        st.markdown(f'<div class="seo-desc-box">{meta_desc}</div>', unsafe_allow_html=True)
        st.caption(f"字符数：{len(meta_desc)} / 建议 120-160")

    with st.expander("📋 复制 SEO 元数据"):
        st.code(f"Title:\n{seo_title}\n\nMeta Description:\n{meta_desc}", language="text")

    st.divider()

    st.markdown('<div class="output-card-title">📄 模块 B — 正文内容</div>',
                unsafe_allow_html=True)
    article = result.get("article", "（未生成）")
    st.markdown(article)
    with st.expander("📋 复制 Markdown 源码"):
        st.code(article, language="markdown")

    st.divider()

    st.markdown('<div class="output-card-title">🎨 模块 C — AI 配图指令</div>',
                unsafe_allow_html=True)
    image_prompts = result.get("image_prompts", [])
    if not image_prompts:
        st.info("暂无配图提示词。")
    else:
        cols = st.columns(min(len(image_prompts), 3))
        for i, item in enumerate(image_prompts):
            with cols[i % len(cols)]:
                scene = item.get("scene", f"场景 {i+1}")
                prompt = item.get("prompt", "")
                st.markdown(f"**🖼️ 场景 {i+1}：{scene}**")
                st.markdown(
                    f'<div class="image-prompt-block">'
                    f'<span class="image-prompt-label">Midjourney / DALL-E Prompt ↓</span>'
                    f'{prompt}'
                    f'<div class="image-prompt-cn">📖 画面说明：{scene}</div>'
                    f'</div>', unsafe_allow_html=True)

        with st.expander("📋 复制全部 Image Prompts"):
            all_prompts = "\n\n".join(
                f"【场景 {i+1}：{it.get('scene','')}】\n{it.get('prompt','')}"
                for i, it in enumerate(image_prompts))
            st.code(all_prompts, language="text")

    st.divider()
    with st.expander("🔧 查看完整 JSON（调试用）"):
        st.json(result)

else:
    st.markdown("""
<div style="text-align:center; padding:60px 20px; color:#4b5563;
    background:#0d1117; border:1px dashed #1f2937; border-radius:12px;">
    <div style="font-size:3rem; margin-bottom:16px;">🌿</div>
    <div style="font-size:1.1rem; color:#6b7280; margin-bottom:8px;">
        在左侧配置 AI 服务商和参数，点击「🚀 生成高质量软文」开始创作
    </div>
    <div style="font-size:0.85rem; color:#374151;">
        支持 Gemini / OpenAI / DeepSeek / Kimi / Claude（via OpenRouter）
    </div>
</div>
""", unsafe_allow_html=True)
