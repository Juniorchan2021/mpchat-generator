from fastapi import HTTPException

from core.scenarios import ARTICLE_STYLES, SCENARIO_CATEGORIES, SP_ID_TO_LABEL


def locate_scenario(category: str, scenario_label: str) -> dict:
    scenarios = SCENARIO_CATEGORIES.get(category, [])
    for scenario in scenarios:
        if scenario["label"] == scenario_label:
            return scenario
    raise HTTPException(status_code=404, detail="Scenario not found")


def style_to_instruction(style_name: str) -> str:
    style = ARTICLE_STYLES.get(style_name)
    if not style:
        raise HTTPException(status_code=404, detail="Style not found")
    return style["instruction"]


def selling_points_text(selling_points: list[str]) -> str:
    labels = [SP_ID_TO_LABEL.get(item, item) for item in selling_points]
    return " / ".join(labels)


def collect_seo_issues(stats: dict) -> list[str]:
    issues: list[str] = []
    if stats.get("h1_count", 0) < 1:
        issues.append("缺少 H1 标题（用 # 开头）")
    if stats.get("h2_count", 0) < 2:
        issues.append(f"H2 段落不足（当前 {stats.get('h2_count', 0)} 个，建议至少 3 个）")
    if not stats.get("has_cta"):
        issues.append("缺少 CTA（如「立即下载」「免费注册」）")
    if stats.get("word_count", 0) < 600:
        issues.append(f"字数偏少（当前 {stats.get('word_count', 0)}，建议 800-1200）")
    keyword_density = stats.get("keyword_density", {})
    low_keywords = [key for key, value in keyword_density.items() if value.get("count", 0) < 2]
    if low_keywords:
        issues.append(f"关键词出现次数不足：{', '.join(low_keywords)}")
    return issues
