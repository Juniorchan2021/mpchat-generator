import os
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

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
        response = requests.get(url, headers=HTTP_HEADERS, timeout=12, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(
            ["script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg", "img", "iframe"]
        ):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)[:max_chars]
    except Exception as exc:
        return f"[抓取失败: {exc}]"


def _fetch_medium_rss(max_items: int = 5, max_chars: int = 3000) -> str:
    try:
        response = requests.get("https://medium.com/feed/@mpchat_blog", headers=HTTP_HEADERS, timeout=12)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        items = root.findall(".//item")[:max_items]
        parts = []
        for item in items:
            title = item.findtext("title", "")
            desc_raw = item.findtext("description", "")
            desc = BeautifulSoup(desc_raw, "html.parser").get_text(strip=True)[:500]
            parts.append(f"📝 {title}\n{desc}")
        return "\n\n".join(parts)[:max_chars]
    except Exception as exc:
        return f"[抓取失败: {exc}]"


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
        response = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(
            ["script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg", "img", "iframe"]
        ):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip() and len(line.strip()) > 15]
        return "\n".join(lines)[:max_chars]
    except Exception as exc:
        return f"[抓取失败: {exc}]"


def _fetch_nitter_twitter(max_chars: int = 2000) -> str:
    nitter_instances = [
        "https://nitter.net/MPChatApp",
        "https://nitter.privacydev.net/MPChatApp",
        "https://nitter.poast.org/MPChatApp",
    ]
    for nitter_url in nitter_instances:
        try:
            response = requests.get(nitter_url, headers=HTTP_HEADERS, timeout=8, allow_redirects=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                tweets = soup.select(".tweet-content, .timeline-item .tweet-body")
                if tweets:
                    parts = [tweet.get_text(strip=True)[:300] for tweet in tweets[:10]]
                    return "\n\n".join(parts)[:max_chars]
        except Exception:
            continue
    return "[抓取失败: Twitter/X 暂不可直接抓取]"


def load_knowledge() -> str:
    root_dir = os.path.dirname(os.path.dirname(__file__))
    kb_path = os.path.join(root_dir, "knowledge.txt")
    if not os.path.exists(kb_path):
        return ""
    with open(kb_path, "r", encoding="utf-8") as file:
        return file.read()


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
    ]

    status_rows: dict[str, dict] = {}
    text_rows: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        future_map = {pool.submit(job): label for label, job in tasks}
        for future in as_completed(future_map):
            label = future_map[future]
            try:
                content = future.result()
            except Exception as exc:
                content = f"[抓取失败: {exc}]"
            text_rows[label] = content
            status_rows[label] = {
                "label": label,
                "ok": not content.startswith("[抓取失败:"),
                "chars": len(content),
            }

    ordered_text = [f"【{label}】\n{text_rows.get(label, '')}" for label, _ in tasks]
    ordered_status = [status_rows[label] for label, _ in tasks]
    return "\n\n".join(ordered_text), ordered_status
