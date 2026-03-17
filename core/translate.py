import logging
import re

from core.generation import call_llm

logger = logging.getLogger(__name__)


def build_translate_prompt(
    article: str,
    source_lang: str,
    target_lang: str,
) -> list[dict]:
    """构建翻译所需的 messages 列表，供 call_llm() 使用。

    要求：
    - 保留完整 Markdown 格式（#/##/###/列表/代码块等）
    - 保留所有标题层级，仅翻译文字内容
    - 术语翻译准确（如 MPChat、mp.net、MP Card 等产品名保持原样）
    - 不添加任何解释或额外内容，直接输出翻译结果
    """
    if not article or not article.strip():
        raise ValueError("article 不能为空")
    if not source_lang or not source_lang.strip():
        raise ValueError("source_lang 不能为空")
    if not target_lang or not target_lang.strip():
        raise ValueError("target_lang 不能为空")
    if source_lang.strip() == target_lang.strip():
        raise ValueError("source_lang 与 target_lang 不能相同")

    system_prompt = f"""你是一位专业的技术内容翻译专家，擅长将 Markdown 格式的文章在不同语言之间精准翻译。

【翻译规则】
1. 严格保留所有 Markdown 语法：
   - 标题层级（# H1、## H2、### H3 等，符号和缩进不变）
   - 列表（- 无序列表、1. 有序列表）
   - 粗体（**text**）、斜体（*text*）、代码（`code`）、代码块（```lang ... ```）
   - 超链接格式 [text](url)（URL 不翻译）
   - 引用块（> text）
2. 产品名称和品牌词保持原样，不翻译：MPChat、MP Card、MP Wallet、mp.net、Stablecoin 等专有名词
3. 仅翻译可读文字内容，不添加任何解释、注释或额外内容
4. 直接输出翻译结果，不要有前言或总结
5. 目标语言：{target_lang.strip()}
"""

    user_prompt = f"""请将以下 {source_lang.strip()} 文章翻译为 {target_lang.strip()}，严格遵守上述翻译规则，直接输出翻译结果：

{article}"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _strip_code_fences(text: str) -> str:
    """剥离 LLM 可能返回的 ``` 代码围栏包装。"""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        inner_lines = lines[1:]
        inner = "\n".join(inner_lines)
        last_fence = inner.rfind("```")
        if last_fence != -1:
            return inner[:last_fence].strip()
        return inner.strip()
    return stripped


def translate_article(
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    article: str,
    source_lang: str,
    target_lang: str,
    max_tokens: int = 16384,
    temperature: float = 0.3,
) -> str:
    """调用 LLM 翻译文章，返回翻译后的 Markdown 字符串。

    参数校验由 build_translate_prompt() 负责（article/source_lang/target_lang）。
    api_key 在此处单独校验，因为它不影响 prompt 构建。
    """
    if not api_key or not api_key.strip():
        raise ValueError("api_key 不能为空")

    messages = build_translate_prompt(article, source_lang, target_lang)

    logger.info(
        "开始翻译文章 | provider=%s model=%s source=%s target=%s chars=%d",
        provider, model, source_lang, target_lang, len(article),
    )

    raw = call_llm(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    result = _strip_code_fences(raw)

    if not result:
        raise ValueError("LLM 返回了空翻译结果")

    logger.info("翻译完成 | result_chars=%d", len(result))
    return result
