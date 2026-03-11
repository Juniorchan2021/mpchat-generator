"""
MPChat v4.0 — GEO (Generative Engine Optimization) tools
Scoring, FAQPage schema, and prompt enhancement.
"""

import json
import re


def geo_score(article: str, faq_pairs: list[dict] | None = None) -> dict:
    """
    Score article for GEO readiness (0-100).
    Checks: answer-first, question H2s, data citations, short paragraphs,
    entity consistency, FAQ presence, authority references.
    """
    lines = article.strip().split("\n")
    non_empty = [ln for ln in lines if ln.strip()]
    score = 0
    issues: list[str] = []
    tips: list[str] = []

    # 1. Answer-First: first non-heading paragraph should be 40-100 chars
    first_para = ""
    for ln in non_empty:
        if not ln.strip().startswith("#"):
            first_para = ln.strip()
            break
    if 40 <= len(first_para) <= 200:
        score += 15
    else:
        issues.append(f"开头段落长度 {len(first_para)} 字，建议 40-100 字直接回答核心问题")
        tips.append("Answer-First：开头直接回答用户最可能的问题")

    # 2. Question-style H2 headers (>=30%)
    h2_lines = [ln.strip() for ln in lines if ln.strip().startswith("## ")]
    question_h2 = [h for h in h2_lines if h.rstrip().endswith("？") or h.rstrip().endswith("?")]
    h2_count = len(h2_lines)
    q_ratio = (len(question_h2) / h2_count * 100) if h2_count else 0
    if q_ratio >= 30:
        score += 15
    elif q_ratio >= 15:
        score += 8
        issues.append(f"问句 H2 占比 {q_ratio:.0f}%，建议 ≥30%")
        tips.append("将部分 H2 改为问句格式（如「MPChat 安全吗？」）")
    else:
        issues.append(f"问句 H2 占比 {q_ratio:.0f}%，远低于 30% 目标")
        tips.append("AI 搜索引擎偏好问答式标题，至少 1/3 的 H2 用问句")

    # 3. Data citations (numbers with sources)
    citation_patterns = [
        r"据.*?(?:报告|研究|数据|统计)",
        r"according to",
        r"\d+%",
        r"\$[\d,.]+",
        r"[\d,.]+ (?:billion|million|万|亿)",
    ]
    citation_count = 0
    for pat in citation_patterns:
        citation_count += len(re.findall(pat, article, re.IGNORECASE))
    citation_count = min(citation_count, 10)
    if citation_count >= 5:
        score += 15
    elif citation_count >= 3:
        score += 10
        issues.append(f"数据引用 {citation_count} 处，建议 ≥5 处")
    else:
        score += max(citation_count * 2, 0)
        issues.append(f"数据引用仅 {citation_count} 处，严重不足")
        tips.append("添加带来源的统计数据（如「据 Chainalysis 2025 报告，稳定币交易额已达 ...」）")

    # 4. Short paragraphs (2-3 sentences each)
    paragraphs = re.split(r"\n\s*\n", article)
    long_paras = [p for p in paragraphs if len(p.strip()) > 300 and not p.strip().startswith("#")]
    if len(long_paras) == 0:
        score += 10
    elif len(long_paras) <= 2:
        score += 6
        issues.append(f"{len(long_paras)} 个段落过长（>300 字），建议拆分")
    else:
        issues.append(f"{len(long_paras)} 个段落过长，不利于 AI 摘要提取")
        tips.append("每段 2-3 句，便于 AI 搜索引擎抓取关键信息")

    # 5. Entity consistency
    entity_names = ["MPChat", "MP Card", "MP Wallet", "mp.net"]
    entity_score = 0
    for name in entity_names:
        if name.lower() in article.lower():
            entity_score += 1
    if entity_score >= 3:
        score += 10
    elif entity_score >= 2:
        score += 6
    else:
        issues.append("产品实体提及不足，建议全文统一使用 MPChat / MP Card / MP Wallet")
        tips.append("AI 搜索引擎通过实体识别建立知识图谱，确保名称一致且频繁出现")

    # 6. FAQ presence
    faq_count = len(faq_pairs) if faq_pairs else 0
    has_faq_section = bool(re.search(r"(?:FAQ|常见问题|Q\s*[:：])", article, re.IGNORECASE))
    if faq_count >= 5 or has_faq_section:
        score += 20
    elif faq_count >= 3:
        score += 12
        issues.append(f"FAQ 仅 {faq_count} 对，建议 5 对")
    else:
        issues.append("缺少 FAQ 段落（AI 搜索引擎高度依赖 Q&A 对）")
        tips.append("在文末加入 5 个 FAQ，每个答案 < 100 字")

    # 7. Authority references
    auth_patterns = [
        r"据.*?(?:表示|指出|研究显示|报告显示)",
        r"according to.*?(?:report|study|research)",
        r"(?:Chainalysis|CoinDesk|Messari|Bloomberg|Reuters)",
    ]
    auth_count = 0
    for pat in auth_patterns:
        auth_count += len(re.findall(pat, article, re.IGNORECASE))
    if auth_count >= 3:
        score += 15
    elif auth_count >= 1:
        score += 8
        issues.append(f"权威引用仅 {auth_count} 处，建议 ≥3 处")
    else:
        issues.append("缺少权威来源引用")
        tips.append("使用「据 [权威机构] 研究显示」框架提升可信度（+32% 引用率）")

    score = min(score, 100)

    return {
        "score": score,
        "issues": issues,
        "tips": tips,
        "details": {
            "answer_first_len": len(first_para),
            "question_h2_ratio": round(q_ratio, 1),
            "citation_count": citation_count,
            "long_paragraphs": len(long_paras),
            "entity_mentions": entity_score,
            "faq_count": faq_count,
            "authority_refs": auth_count,
        },
    }


def generate_faq_schema(faq_pairs: list[dict]) -> str:
    """Generate FAQPage JSON-LD schema from Q&A pairs."""
    if not faq_pairs:
        return "{}"
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": pair.get("q", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": pair.get("a", ""),
                },
            }
            for pair in faq_pairs
            if pair.get("q")
        ],
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def build_geo_optimize_prompt(article: str, geo_result: dict, keywords: str = "") -> str:
    """Build prompt for one-click GEO optimization."""
    issues_text = "\n".join(f"- {iss}" for iss in geo_result["issues"])
    tips_text = "\n".join(f"- {tip}" for tip in geo_result["tips"])

    return f"""请优化以下文章的 GEO（Generative Engine Optimization）表现，目标评分 90-100 分。

【当前 GEO 评分】{geo_result['score']}/100

【需修复的问题】
{issues_text if issues_text else '- 整体需要优化'}

【优化方向】
{tips_text if tips_text else '- 全面增强 GEO 指标'}

【GEO 优化规范】
1. Answer-First：开头 40-100 字直接回答核心问题
2. 问句 H2：至少 30% 的 H2 用问句
3. 数据引用：5+ 个带来源的统计数据
4. FAQ：在文末加 5 个 Q&A 对，每答案 < 100 字
5. 短段落：每段 2-3 句
6. 权威引用：3+ 处「据 [来源] 研究显示」
7. 实体一致：MPChat / MP Card / MP Wallet 全文统一

【SEO 关键词（需保留）】
{keywords if keywords else 'MPChat, 加密支付'}

【原文】
{article}

请直接输出优化后的完整文章（Markdown 格式），不要输出 JSON，不要解释修改内容。
在文末加入 FAQ 段落（## 常见问题），包含 5 个 Q&A。"""


def build_dual_optimize_prompt(
    article: str,
    seo_stats: dict,
    geo_result: dict,
    keywords: str = "",
) -> str:
    """Build prompt for combined SEO + GEO optimization to 90+ on both."""
    seo_issues: list[str] = []
    if seo_stats.get("h1_count", 0) < 1:
        seo_issues.append("缺少 H1 标题")
    if seo_stats.get("h2_count", 0) < 3:
        seo_issues.append(f"H2 段落不足（当前 {seo_stats.get('h2_count', 0)} 个，需 ≥3）")
    if not seo_stats.get("has_cta"):
        seo_issues.append("缺少 CTA")
    if seo_stats.get("word_count", 0) < 600:
        seo_issues.append(f"字数偏少（{seo_stats.get('word_count', 0)}）")
    kw_density = seo_stats.get("keyword_density", {})
    low_kw = [k for k, v in kw_density.items() if v.get("count", 0) < 2]
    if low_kw:
        seo_issues.append(f"关键词密度不足：{', '.join(low_kw)}")

    geo_issues = geo_result.get("issues", [])

    seo_text = "\n".join(f"- {i}" for i in seo_issues) if seo_issues else "- 无严重问题"
    geo_text = "\n".join(f"- {i}" for i in geo_issues) if geo_issues else "- 无严重问题"

    return f"""请同时优化以下文章的 SEO 和 GEO 表现，目标：两项评分均达到 90-100 分。

⚠️ 关键约束：SEO 和 GEO 必须同时兼顾，不能为了提升一项而牺牲另一项。

【当前 SEO 评分】{seo_stats.get('structure_score', 0)}/100
【当前 GEO 评分】{geo_result['score']}/100

【SEO 问题】
{seo_text}

【GEO 问题】
{geo_text}

【SEO 优化要求（必须满足）】
1. 1 个 H1（#）+ 至少 3 个 H2（##）
2. 关键词密度 1-2%（关键词：{keywords if keywords else 'MPChat, 加密支付'}）
3. 结尾有明确 CTA（引导下载 MPChat 或申请 MP Card）
4. 总长度 800-1200 字，每段 ≤150 字

【GEO 优化要求（必须满足）】
1. Answer-First：开头 40-100 字直接回答核心问题
2. 问句 H2：至少 30% 的 H2 使用问句
3. 数据引用：5+ 个带来源的统计数据
4. 短段落：每段 2-3 句
5. 权威引用：3+ 处「据 [来源] 研究显示」
6. 实体一致：全文统一使用 MPChat / MP Card / MP Wallet
7. 文末 FAQ：加入「## 常见问题」段落，包含 5 个 Q&A，每答案 < 100 字

【兼容策略】
- H2 标题：用问句格式（满足 GEO）+ 含关键词（满足 SEO）
- 段落：短段落（满足 GEO）+ 自然植入关键词（满足 SEO）
- 数据引用同时提升 GEO 可信度和 SEO 内容质量
- FAQ 段落同时满足 GEO 的 Q&A 需求和 SEO 的长尾关键词覆盖

【原文】
{article}

请直接输出优化后的完整文章（Markdown 格式），不要输出 JSON，不要解释修改内容。"""
