from core.generation import (
    build_ai_detect_prompt,
    build_seo_optimize_prompt,
    call_llm,
    get_client,
    parse_opt_result,
)
from core.geo_tools import build_dual_optimize_prompt, build_geo_optimize_prompt, build_triple_optimize_prompt, geo_score
from core.seo_tools import reading_stats

JSON_OPT_INSTRUCTION = """

请以 JSON 格式输出，包含两个字段：
{
  "optimized_article": "优化后的完整 Markdown 文章",
  "changelog": [
    "具体修改1的描述",
    "具体修改2的描述"
  ]
}
"""


def optimize_article_content(
    article: str,
    keywords: str,
    mode: str,
    api_key: str,
    model: str,
    base_url: str = "",
    provider: str = "",
) -> dict:
    seo_before = reading_stats(article, keywords).get("structure_score", 0)
    geo_before = geo_score(article, [])["score"]
    seo_stats = reading_stats(article, keywords)
    geo_result = geo_score(article, [])

    if mode == "seo":
        prompt = build_seo_optimize_prompt(article, keywords, [])
        system_message = "你是 SEO 优化专家。请严格输出 JSON。"
    elif mode == "geo":
        prompt = build_geo_optimize_prompt(article, geo_result, keywords=keywords) + JSON_OPT_INSTRUCTION
        system_message = "你是 GEO 内容优化专家。请严格输出 JSON。"
    elif mode == "triple":
        prompt = build_triple_optimize_prompt(article, seo_stats, geo_result, keywords=keywords or "MPChat, mp.net")
        prompt += JSON_OPT_INSTRUCTION
        system_message = "你是 SEO、GEO 与人性化写作专家。请严格输出 JSON。"
    elif mode == "humanize":
        prompt = f"""请将以下文章进行人性化改写，目标：降低 AI 检测率，同时保留 H1/H2/FAQ/CTA、关键词与产品实体。

【关键词】
{keywords or 'MPChat, mp.net'}

【原文】
{article}
{JSON_OPT_INSTRUCTION}"""
        system_message = "你是资深人类内容编辑。请严格输出 JSON。"
    else:
        prompt = build_dual_optimize_prompt(article, seo_stats, geo_result, keywords=keywords or "MPChat, mp.net")
        prompt += JSON_OPT_INSTRUCTION
        system_message = "你是 SEO + GEO 联合优化专家。请严格输出 JSON。"

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]
    if provider:
        raw = call_llm(provider=provider, api_key=api_key, base_url=base_url,
                        model=model, messages=messages, max_tokens=16000, temperature=0.6)
    else:
        client = get_client(api_key, base_url)
        response = client.chat.completions.create(
            model=model, messages=messages, temperature=0.6, max_tokens=16000,
        )
        raw = response.choices[0].message.content.strip()
    optimized_article, changelog = parse_opt_result(raw)
    seo_after = reading_stats(optimized_article, keywords).get("structure_score", 0)
    geo_after = geo_score(optimized_article, [])["score"]
    return {
        "optimized_article": optimized_article,
        "changelog": changelog,
        "seo_before": seo_before,
        "seo_after": seo_after,
        "geo_before": geo_before,
        "geo_after": geo_after,
    }


def detect_ai_content(article: str, api_key: str, model: str, base_url: str = "", provider: str = "") -> str:
    messages = [
        {"role": "system", "content": "你是 AI 内容检测专家，擅长分析文本是否由 AI 生成。"},
        {"role": "user", "content": build_ai_detect_prompt(article)},
    ]
    if provider:
        return call_llm(provider=provider, api_key=api_key, base_url=base_url,
                         model=model, messages=messages, max_tokens=2000, temperature=0.3)
    else:
        client = get_client(api_key, base_url)
        response = client.chat.completions.create(
            model=model, messages=messages, temperature=0.3, max_tokens=2000,
        )
        return response.choices[0].message.content.strip()
