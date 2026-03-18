import json
import re

from openai import OpenAI

from core.knowledge import load_knowledge
from core.scenarios import LANGUAGES

KNOWLEDGE = load_knowledge()


def get_client(api_key: str, base_url: str = "") -> OpenAI:
    kwargs = {"api_key": api_key}
    if base_url.strip():
        kwargs["base_url"] = base_url.strip()
    return OpenAI(**kwargs)


def call_llm(
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    messages: list[dict],
    max_tokens: int = 16384,
    temperature: float = 0.7,
    response_format: dict | None = None,
) -> str:
    """Unified LLM call that handles Anthropic separately from OpenAI-compatible providers."""
    if provider == "anthropic":
        try:
            from anthropic import Anthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic>=0.40.0")
        client = Anthropic(api_key=api_key)
        system_msg = ""
        user_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                user_msgs.append(m)
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_msg,
            messages=user_msgs,
        )
        if not resp.content:
            raise ValueError("Anthropic returned empty response")
        return resp.content[0].text
    else:
        client = get_client(api_key, base_url)
        kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format
        try:
            resp = client.chat.completions.create(**kwargs)
        except Exception as e:
            err_msg = str(e).lower()
            if "response_format" in err_msg or "json_object" in err_msg or "unsupported" in err_msg:
                kwargs.pop("response_format", None)
                resp = client.chat.completions.create(**kwargs)
            else:
                raise
        content = resp.choices[0].message.content if resp.choices else None
        if not content:
            raise ValueError("LLM returned empty response")
        return content


def geo_prompt_section() -> str:
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


def build_system_prompt(
    language: str,
    style_instruction: str,
    scenario_label: str,
    web_content: str = "",
    geo_mode: bool = False,
    word_count_target: int = 1200,
) -> str:
    lang_cfg = LANGUAGES.get(language, LANGUAGES["中文 (Chinese)"])
    lang_instruction = lang_cfg["instruction"]
    web_section = (
        f"\n\n【实时网络资料（来自 mp.net 官网 / Medium / Twitter / Google / 百度）】\n{web_content[:8000]}"
        if web_content.strip()
        else ""
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
- 文章总长度：{word_count_target} 字左右（中文）/ 相应词数（英文）
- 结尾必须有清晰有力的 CTA（Call to Action），引导用户访问 mp.net 下载 MPChat 或申请 MP Card（官网是 mp.net，不是 mpchat.io）

【输出格式要求（严格遵守 JSON 格式）】
请以合法的 JSON 格式输出，结构如下：
{{
  "seo_title": "文章 SEO 标题（50-60 字符，含核心关键词）",
  "meta_description": "元描述（120-160 字符，总结文章价值并含关键词）",
  "slug_suggestion": "url-friendly-slug-in-english",
  "title_alternatives": ["备选标题1", "备选标题2", "备选标题3"],
  "article": "完整文章正文（Markdown 格式，含 H1/H2/CTA）",
  "faq_pairs": [{{"q": "问题", "a": "回答"}}],
  "image_prompts": [
    {{
      "scene": "场景描述（中文）",
      "prompt": "英文 Midjourney/DALL-E 提示词（详细、专业、含风格/光线/构图）"
    }}
  ],
  "image_search_terms": ["英文Pixabay搜索词1", "英文搜索词2", "英文搜索词3"]
}}

【title_alternatives 规范】
- 提供 3 个与主标题不同角度的备选标题
- 每个标题都要包含核心关键词，但切入角度不同

【Image Prompt 规范】
- 必须是纯英文
- 必须包含：主体描述 + 环境背景 + 光影效果 + 艺术风格 + 质量标签
- 生成 2-3 个不同场景的 Prompt

【image_search_terms 规范】
- 提供 5 个英文搜索短语（2-4 个词），用于 Pixabay / Pexels 搜索配图
- 每个短语必须与文章具体内容相关，而非泛泛的通用词
- 5 个短语要覆盖不同的视觉场景
""" + (geo_prompt_section() if geo_mode else "")


def build_user_prompt(
    language: str,
    scenario_label: str,
    audience_tag: str,
    selling_points_text: str,
    style_name: str,
    keywords: str,
    target_title: str = "",
) -> str:
    keyword_text = keywords.strip() if keywords.strip() else "MPChat, 加密支付, 稳定币"
    title_instruction = (
        f"\n- 目标标题（必须严格以此标题为 H1，不得修改）：{target_title.strip()}"
        if target_title and target_title.strip()
        else ""
    )
    return f"""请根据以下参数，生成一篇完整的 MPChat 推广软文和配套 AI 绘画提示词。

【生成参数】
- 输出语言：{language}
- 写作场景：{scenario_label}
- 目标受众：{audience_tag}
- 主打卖点：{selling_points_text}
- 文章文风：{style_name}
- SEO 核心关键词：{keyword_text}{title_instruction}

请严格按照系统提示中规定的 JSON 格式输出，确保 JSON 合法可解析。
"""


def strip_code_fences(text: str) -> str:
    if text.startswith("```"):
        lines = text.split("\n")
        inner = "\n".join(lines[1:])
        if "```" in inner:
            return inner[: inner.rfind("```")].strip()
        return inner.strip()
    return text


def extract_json_field(raw: str, field: str) -> str | None:
    pattern = rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"'
    match = re.search(pattern, raw, re.DOTALL)
    if not match:
        return None
    value = match.group(1)
    value = value.replace("\\n", "\n").replace("\\t", "\t")
    value = value.replace('\\"', '"').replace("\\\\", "\\")
    return value


def extract_json_array(raw: str, field: str) -> list[str] | None:
    pattern = rf'"{field}"\s*:\s*\[(.*?)\]'
    match = re.search(pattern, raw, re.DOTALL)
    if not match:
        return None
    return re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1))


def robust_parse(raw: str) -> dict:
    for candidate in (
        raw,
        re.sub(r",\s*}", "}", raw),
    ):
        candidate = re.sub(r",\s*]", "]", candidate)
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            pass

    try:
        collapsed = raw.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
        return json.loads(collapsed)
    except (json.JSONDecodeError, ValueError):
        pass

    article = extract_json_field(raw, "article")
    if article:
        result: dict = {"article": article}
        for field in ("seo_title", "meta_description", "slug_suggestion"):
            value = extract_json_field(raw, field)
            if value:
                result[field] = value
        result["title_alternatives"] = extract_json_array(raw, "title_alternatives") or []
        result["image_search_terms"] = extract_json_array(raw, "image_search_terms") or ["crypto payment"]
        result.setdefault("faq_pairs", [])
        result.setdefault("image_prompts", [])
        result.setdefault("seo_title", "MPChat — Live with Crypto")
        result.setdefault("meta_description", "")
        result.setdefault("slug_suggestion", "mpchat-article")
        return result

    cleaned = raw.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\\")
    return {
        "seo_title": extract_json_field(raw, "seo_title") or "MPChat — Live with Crypto",
        "meta_description": extract_json_field(raw, "meta_description") or "",
        "slug_suggestion": extract_json_field(raw, "slug_suggestion") or "mpchat-article",
        "article": cleaned,
        "image_prompts": [],
        "image_search_terms": extract_json_array(raw, "image_search_terms") or ["crypto payment"],
        "title_alternatives": extract_json_array(raw, "title_alternatives") or [],
        "faq_pairs": [],
    }


def validate_keywords(keywords: str) -> str | None:
    text = keywords.strip()
    if not text:
        return "关键词不能为空，请输入至少一个关键词。"
    if len(text) < 2:
        return "关键词至少需要 2 个字符。"
    if len(text) > 500:
        return "关键词总长度不能超过 500 个字符。"
    if re.search(r"""[<>"'`]""", text):
        return "关键词包含非法字符（< > \" ' `），请移除后重试。"
    if re.match(r"^[\s\d,，、]+$", text):
        return "关键词不能只包含数字或分隔符，请输入有意义的关键词。"
    return None


def generate_article(
    client: OpenAI = None,
    model: str = "",
    language: str = "",
    scenario_label: str = "",
    audience_tag: str = "",
    selling_points_text: str = "",
    style_name: str = "",
    style_instruction: str = "",
    keywords: str = "",
    web_content: str = "",
    geo_mode: bool = False,
    word_count_target: int = 1200,
    provider: str = "",
    api_key: str = "",
    base_url: str = "",
    target_title: str = "",
) -> dict:
    system_prompt = build_system_prompt(
        language, style_instruction, scenario_label, web_content,
        geo_mode=geo_mode, word_count_target=word_count_target,
    )
    user_prompt = build_user_prompt(
        language, scenario_label, audience_tag, selling_points_text,
        style_name, keywords, target_title=target_title,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    if provider and api_key:
        raw_text = call_llm(
            provider=provider, api_key=api_key, base_url=base_url,
            model=model, messages=messages, max_tokens=16384, temperature=0.82,
            response_format={"type": "json_object"} if provider != "anthropic" else None,
        )
    elif client:
        try:
            response = client.chat.completions.create(
                model=model, messages=messages,
                temperature=0.82, max_tokens=16384,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            err_msg = str(e).lower()
            if any(k in err_msg for k in ("json_object", "response_format", "not support", "unsupported")):
                response = client.chat.completions.create(
                    model=model, messages=messages,
                    temperature=0.82, max_tokens=16384,
                )
            else:
                raise
        _content = response.choices[0].message.content if response.choices else None
        if not _content:
            raise ValueError("LLM returned empty response")
        raw_text = _content.strip()
    else:
        raise ValueError("Either (provider + api_key) or client must be provided")

    raw = strip_code_fences(raw_text.strip())
    if not raw.startswith("{"):
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            raw = match.group(0)
    return robust_parse(raw)


def build_seo_optimize_prompt(article: str, keywords: str, issues: list[str]) -> str:
    issue_block = "\n".join(f"- {issue}" for issue in issues) if issues else "- 整体结构需要优化"
    return f"""请优化以下文章的 SEO 表现，目标评分 90-100 分。

【当前问题】
{issue_block}

【SEO 优化要求】
- 确保有 1 个 H1（#）和至少 3 个 H2（##）
- 自然增加关键词密度到 1-2%（关键词：{keywords or 'MPChat, mp.net'}）
- 结尾必须有明确的 CTA（引导访问 mp.net）
- 文章总长度 800-1200 字
- 每段不超过 150 字

【原文】
{article}

请直接输出优化后的完整 Markdown 文章，不要解释修改内容。
"""


def parse_opt_result(raw: str) -> tuple[str, list[str]]:
    if not raw:
        raise ValueError("AI returned empty optimization result")
    cleaned = strip_code_fences(raw.strip())
    for candidate in (
        cleaned,
        re.sub(r",\s*}", "}", cleaned),
    ):
        candidate = re.sub(r",\s*]", "]", candidate)
        try:
            data = json.loads(candidate)
            if isinstance(data, dict) and data.get("optimized_article"):
                changelog = data.get("changelog") or []
                return data["optimized_article"], changelog if isinstance(changelog, list) else []
        except (json.JSONDecodeError, ValueError):
            pass

    match = re.search(r'"optimized_article"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned, re.DOTALL)
    if match:
        article = match.group(1).replace("\\n", "\n").replace('\\"', '"')
        changelog_match = re.findall(r'"changelog"\s*:\s*\[(.*?)\]', cleaned, re.DOTALL)
        changelog = re.findall(r'"((?:[^"\\]|\\.)*)"', changelog_match[0]) if changelog_match else []
        return article, changelog
    if cleaned.startswith("#") or "\n##" in cleaned or len(cleaned) > 200:
        return cleaned, ["AI 返回了非 JSON 格式，已直接使用返回内容"]
    raise ValueError("无法从 AI 响应中提取优化后的文章")


def build_ai_detect_prompt(article: str) -> str:
    return f"""请分析以下文章，评估其被 AI 检测工具判定为 AI 生成内容的可能性。

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
