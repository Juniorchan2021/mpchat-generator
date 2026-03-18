import json
import logging
import re

from core.generation import call_llm

logger = logging.getLogger(__name__)


def build_ideation_prompt(
    core_keyword: str,
    industry: str,
    count: int,
    language: str = "auto",
) -> list[dict]:
    """构建 SEO 选题生成的 messages 列表，供 call_llm() 使用。

    输出 JSON 数组，每项含：title, search_intent, difficulty, keywords
    language: "auto"=自动检测, "zh"=中文, "en"=英文, 其他语言代码
    """
    if not core_keyword or not core_keyword.strip():
        raise ValueError("core_keyword 不能为空")
    if count <= 0:
        raise ValueError("count 必须大于 0")
    if count > 50:
        raise ValueError("count 不能超过 50")

    industry_clause = f"，聚焦 {industry.strip()} 行业" if industry and industry.strip() else ""

    # 根据 language 参数确定标题语言指令
    if language == "auto":
        # 自动检测：若关键词含中文字符则用中文，否则用英文
        has_chinese = bool(re.search(r"[\u4e00-\u9fff]", core_keyword))
        lang_instruction = "使用中文生成标题" if has_chinese else "generate titles in English"
    elif language == "zh":
        lang_instruction = "使用中文生成标题"
    elif language == "en":
        lang_instruction = "generate titles in English"
    else:
        lang_instruction = f"generate titles in {language}"

    system_prompt = f"""你是一位专业的 SEO 内容策略专家，擅长基于核心关键词生成高价值的博客选题列表。

【输出要求】
- 严格输出 JSON 数组，不包含任何额外文字或 Markdown 围栏
- 数组中每个元素包含以下字段：
  - title (string)：吸引人的博客标题，包含核心关键词（{lang_instruction}）
  - search_intent (string)：搜索意图，取值之一：informational / commercial / transactional / navigational
  - difficulty (string)：SEO 竞争难度，取值之一：easy / medium / hard
  - keywords (array of string)：该标题相关的 3-5 个关键词
- 标题应多样化，覆盖不同搜索意图和难度层次
- 标题应具体、有价值，避免泛泛而谈
"""

    user_prompt = f"""请基于核心关键词 "{core_keyword.strip()}"{industry_clause}，生成 {count} 个 SEO 博客选题。

直接输出 JSON 数组，格式示例：
[
  {{
    "title": "How to Use Crypto Payment for E-Commerce in 2025",
    "search_intent": "informational",
    "difficulty": "medium",
    "keywords": ["crypto payment", "e-commerce", "2025", "bitcoin", "stablecoin"]
  }}
]"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def parse_topics(raw: str) -> list[dict]:
    """从 LLM 返回的原始字符串中解析 topic 列表。

    依次尝试：直接 JSON 解析 → 剥离代码围栏后解析 → 正则提取数组后解析。
    任何失败均返回空列表，不抛出异常。
    """
    if not raw or not raw.strip():
        return []

    # 剥离 ```json ... ``` 或 ``` ... ``` 包裹
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
                return _normalize_topics(parsed)
        except (json.JSONDecodeError, ValueError):
            pass

    # 正则从文本中提取第一个 JSON 数组
    match = re.search(r"\[[\s\S]*\]", raw)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, list):
                return _normalize_topics(parsed)
        except (json.JSONDecodeError, ValueError):
            pass

    return []


def _normalize_topics(items: list) -> list[dict]:
    """确保每个 topic 字段完整，keywords 始终为 list。"""
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        keywords = item.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",") if k.strip()]
        result.append({
            "title": str(item.get("title", "")),
            "search_intent": str(item.get("search_intent", "informational")),
            "difficulty": str(item.get("difficulty", "medium")),
            "keywords": keywords if isinstance(keywords, list) else [],
        })
    return result


def generate_topics(
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    core_keyword: str,
    industry: str = "",
    count: int = 30,
    language: str = "auto",
) -> list[dict]:
    """调用 LLM 生成 SEO 选题列表，返回 list[dict]。

    参数校验由 build_ideation_prompt() 负责（core_keyword, count）。
    api_key 在此处单独校验。
    language: "auto"=根据关键词语言自动判断, "zh"=中文, "en"=英文
    LLM 解析失败时返回空列表，不抛出异常。
    """
    if not api_key or not api_key.strip():
        raise ValueError("api_key 不能为空")

    messages = build_ideation_prompt(core_keyword, industry, count, language)

    logger.info(
        "开始生成选题 | provider=%s model=%s keyword=%s count=%d",
        provider, model, core_keyword, count,
    )

    raw = call_llm(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
        messages=messages,
        max_tokens=8192,
        temperature=0.8,
    )

    topics = parse_topics(raw)
    logger.info("选题生成完成 | count=%d", len(topics))
    return topics
