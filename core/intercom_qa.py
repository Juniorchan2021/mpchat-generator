import json
import logging
import re

import requests

from core.generation import call_llm

logger = logging.getLogger(__name__)

_INTERCOM_ARTICLES_URL = "https://api.intercom.io/articles"

DEFAULT_LANGUAGES = ["zh", "zh-TW", "en"]

LANGUAGE_NAMES: dict[str, str] = {
    "zh": "简体中文",
    "zh-TW": "繁体中文",
    "en": "English",
}


def plaintext_to_html(text: str) -> str:
    """将纯文本转换为简单 HTML，供上传 Intercom 使用。

    规则：
    - 以 "- " 或 "* " 开头的行识别为无序列表项，合并为 <ul><li>...</li></ul>
    - 以数字+点开头（"1. "）的行识别为有序列表项，合并为 <ol><li>...</li></ul>
    - 其余非空行包装为 <p>...</p>
    - 连续空行折叠为单次段落分隔
    """
    if not text or not text.strip():
        return ""

    # 如果已包含 HTML 标签，直接返回（避免双重转换）
    if re.search(r"<(p|ul|ol|li|strong|em|h[1-6])\b", text):
        return text.strip()

    lines = text.strip().splitlines()
    result: list[str] = []
    ul_items: list[str] = []
    ol_items: list[str] = []

    def _flush_ul() -> None:
        if ul_items:
            result.append("<ul>" + "".join(f"<li>{item}</li>" for item in ul_items) + "</ul>")
            ul_items.clear()

    def _flush_ol() -> None:
        if ol_items:
            result.append("<ol>" + "".join(f"<li>{item}</li>" for item in ol_items) + "</ol>")
            ol_items.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            _flush_ul()
            _flush_ol()
            continue

        if re.match(r"^[-*]\s+(.+)", stripped):
            _flush_ol()
            item = re.match(r"^[-*]\s+(.+)", stripped).group(1)
            ul_items.append(item)
        elif re.match(r"^\d+\.\s+(.+)", stripped):
            _flush_ul()
            item = re.match(r"^\d+\.\s+(.+)", stripped).group(1)
            ol_items.append(item)
        else:
            _flush_ul()
            _flush_ol()
            result.append(f"<p>{stripped}</p>")

    _flush_ul()
    _flush_ol()

    return "".join(result)


def build_qa_generation_prompt(
    feature_description: str,
    product_name: str,
    tone: str,
    count: int,
    languages: list[str] | None = None,
) -> list[dict]:
    """构建 Intercom 帮助中心 QA 生成的 messages 列表，供 call_llm() 使用。

    输出多语言嵌套 JSON 对象：
    {
      "zh": [...QA pairs...],
      "zh-TW": [...QA pairs...],
      "en": [...QA pairs...]
    }
    每个 QA pair 含：question, answer（纯文本，无 HTML 标签）, category
    """
    if not feature_description or not feature_description.strip():
        raise ValueError("feature_description 不能为空")
    if count <= 0:
        raise ValueError("count 必须大于 0")
    if count > 50:
        raise ValueError("count 不能超过 50")

    if languages is None:
        languages = DEFAULT_LANGUAGES

    product_clause = product_name.strip() if product_name and product_name.strip() else "the product"

    lang_labels = [LANGUAGE_NAMES.get(lang, lang) for lang in languages]
    lang_list_str = "、".join(lang_labels)

    system_prompt = f"""You are a professional technical writer specializing in help center documentation for SaaS products.
Your task is to generate high-quality Q&A pairs for an Intercom Help Center in multiple languages simultaneously.

【Output Requirements】
- Output ONLY a valid JSON object (not an array), no additional text or Markdown fences
- The object must have exactly {len(languages)} keys: {json.dumps(languages)}
- Each key maps to an array of Q&A pair objects
- Each Q&A pair object must contain:
  - question (string): a clear, specific question a user might ask, written in the language of that key
  - answer (string): a helpful, accurate answer in PLAIN TEXT only — NO HTML tags whatsoever
  - category (string): a logical help center category (e.g. "Getting Started", "Payments", "Account", "Troubleshooting") — always written in English
- Tone: friendly and approachable, using simple language
- Product name: {product_clause}
- Questions should cover: how-to, troubleshooting, feature explanation, limits/requirements
- Answers should be complete and actionable, written in {lang_list_str} respectively
- All language versions must cover the same topics; translations must be natural, not word-for-word
"""

    lang_example_key = languages[0]
    lang_example_q = "如何用 MPChat 发送 USDC？" if lang_example_key == "zh" else (
        "如何使用 MPChat 傳送 USDC？" if lang_example_key == "zh-TW" else
        f"How do I send USDC using {product_clause}?"
    )
    lang_example_a = "打开 MPChat，点击发送按钮，输入收款地址和金额，确认后即可完成转账。" if lang_example_key == "zh" else (
        "開啟 MPChat，點擊傳送按鈕，輸入收款地址和金額，確認後即可完成轉帳。" if lang_example_key == "zh-TW" else
        f"Open {product_clause}, tap the Send button, enter the recipient address and amount, then confirm."
    )

    user_prompt = f"""Generate {count} Q&A pairs per language for the following feature of {product_clause}:

Feature Description:
{feature_description.strip()}

Output a JSON object with keys {json.dumps(languages)}, each containing an array of {count} Q&A pairs.

Example format:
{{
  "{lang_example_key}": [
    {{
      "question": "{lang_example_q}",
      "answer": "{lang_example_a}",
      "category": "Payments"
    }}
  ]
}}

IMPORTANT: answers must be plain text only — absolutely no HTML tags."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def parse_qa_pairs(raw: str) -> list[dict]:
    """从 LLM 返回的原始字符串中解析单语言 QA 列表（向后兼容保留）。

    依次尝试：直接 JSON 解析 → 剥离代码围栏后解析 → 正则提取数组后解析。
    任何失败均返回空列表，不抛出异常。
    """
    if not raw or not raw.strip():
        return []

    stripped = raw.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        inner = "\n".join(lines[1:])
        last_fence = inner.rfind("```")
        if last_fence != -1:
            inner = inner[:last_fence]
        stripped = inner.strip()

    for candidate in (stripped, raw.strip()):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return _normalize_qa_pairs(parsed)
        except (json.JSONDecodeError, ValueError):
            pass

    match = re.search(r"\[[\s\S]*\]", raw)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, list):
                return _normalize_qa_pairs(parsed)
        except (json.JSONDecodeError, ValueError):
            pass

    return []


def parse_qa_result(raw: str, languages: list[str]) -> dict[str, list[dict]]:
    """从 LLM 返回的原始字符串中解析多语言 QA 结构。

    期望输出格式：{ "zh": [...], "zh-TW": [...], "en": [...] }
    任何解析失败均返回每个语言对应空列表，不抛出异常。
    """
    empty: dict[str, list[dict]] = {lang: [] for lang in languages}

    if not raw or not raw.strip():
        return empty

    stripped = raw.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        inner = "\n".join(lines[1:])
        last_fence = inner.rfind("```")
        if last_fence != -1:
            inner = inner[:last_fence]
        stripped = inner.strip()

    for candidate in (stripped, raw.strip()):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                result: dict[str, list[dict]] = {}
                for lang in languages:
                    items = parsed.get(lang, [])
                    result[lang] = _normalize_qa_pairs(items) if isinstance(items, list) else []
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    # 正则从文本中提取第一个 JSON 对象
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, dict):
                result = {}
                for lang in languages:
                    items = parsed.get(lang, [])
                    result[lang] = _normalize_qa_pairs(items) if isinstance(items, list) else []
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    return empty


def _normalize_qa_pairs(items: list) -> list[dict]:
    """确保每个 QA 对字段完整，过滤非字典条目。"""
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        result.append({
            "question": str(item.get("question", "")),
            "answer": str(item.get("answer", "")),
            "category": str(item.get("category", "General")),
        })
    return result


def generate_qa_pairs(
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    feature_description: str,
    product_name: str = "",
    tone: str = "friendly",
    count: int = 10,
    languages: list[str] | None = None,
) -> dict[str, list[dict]]:
    """调用 LLM 生成多语言 Intercom 帮助中心 QA，返回 dict[lang, list[dict]]。

    参数校验由 build_qa_generation_prompt() 负责。
    api_key 在此处单独校验。
    LLM 解析失败时各语言返回空列表，不抛出异常。
    """
    if not api_key or not api_key.strip():
        raise ValueError("api_key 不能为空")

    if languages is None:
        languages = DEFAULT_LANGUAGES

    messages = build_qa_generation_prompt(feature_description, product_name, tone, count, languages)

    logger.info(
        "开始生成多语言 QA | provider=%s model=%s count=%d languages=%s",
        provider, model, count, languages,
    )

    raw = call_llm(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
        messages=messages,
        max_tokens=8192,
        temperature=0.7,
    )

    qa_by_language = parse_qa_result(raw, languages)
    total = sum(len(v) for v in qa_by_language.values())
    logger.info("QA 生成完成 | total=%d", total)
    return qa_by_language


def upload_to_intercom(
    token: str,
    collection_id: str,
    title: str,
    body: str,
    state: str = "published",
    locale: str = "zh",
) -> dict:
    """将文章上传到 Intercom Help Center。

    body 支持纯文本或 HTML；纯文本会自动转换为 HTML。
    locale 参数指定文章语言（zh / zh-TW / en）。
    返回 Intercom API 响应字典（含 id、title 等字段）。
    失败时抛出异常。
    """
    if not token or not token.strip():
        raise ValueError("token 不能为空")
    if not title or not title.strip():
        raise ValueError("title 不能为空")
    if not body or not body.strip():
        raise ValueError("body 不能为空")

    html_body = plaintext_to_html(body)

    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Intercom-Version": "2.11",
    }

    payload: dict = {
        "title": title.strip(),
        "body": html_body,
        "state": state,
    }
    if locale and locale.strip():
        payload["locale"] = locale.strip()
    if collection_id and collection_id.strip():
        payload["parent_id"] = int(collection_id) if collection_id.strip().isdigit() else collection_id.strip()
        payload["parent_type"] = "collection"

    logger.info("上传文章到 Intercom | title=%s collection=%s locale=%s", title, collection_id, locale)

    resp = requests.post(_INTERCOM_ARTICLES_URL, json=payload, headers=headers, timeout=30)

    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Intercom API 返回 {resp.status_code}: {resp.text[:200]}"
        )

    return resp.json()


_INTERCOM_COLLECTIONS_URL = "https://api.intercom.io/help_center/collections"


def fetch_intercom_collections(token: str) -> list[dict]:
    """从 Intercom Help Center API 获取所有 Collection 列表。

    返回规范化后的列表，每项含：
    - id (str)
    - name (str)：默认名称
    - translated_content (dict)：各语言名称 {locale: name_str}

    失败时抛出异常。
    """
    if not token or not token.strip():
        raise ValueError("token 不能为空")

    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Accept": "application/json",
        "Intercom-Version": "2.11",
    }

    logger.info("获取 Intercom Collections")

    resp = requests.get(_INTERCOM_COLLECTIONS_URL, headers=headers, timeout=15)

    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Intercom API 返回 {resp.status_code}: {resp.text[:200]}"
        )

    data = resp.json()
    raw_items = data.get("data", [])

    result: list[dict] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        translated: dict[str, str] = {}
        tc = item.get("translated_content") or {}
        if isinstance(tc, dict):
            for locale_key, locale_val in tc.items():
                if isinstance(locale_val, dict):
                    name_str = locale_val.get("name", "")
                    if name_str:
                        translated[locale_key] = name_str
        result.append({
            "id": str(item.get("id", "")),
            "name": str(item.get("name", "")),
            "translated_content": translated,
        })

    logger.info("获取 Collections 完成 | count=%d", len(result))
    return result
