from pydantic import BaseModel


class ProviderResponse(BaseModel):
    id: str
    label: str
    base_url: str
    models: list[str]
    key_prefix: str
    get_key_url: str


class ConfigResponse(BaseModel):
    providers: list[ProviderResponse]
    scenario_categories: dict
    article_styles: dict
    keyword_presets: list[dict]
    languages: dict
    selling_point_groups: dict


class GenerateResponse(BaseModel):
    title: str
    meta_description: str
    slug: str
    ab_titles: list[str]
    article: str
    faq_pairs: list[dict]
    images: list[dict]
    image_prompts: list[dict]
    image_search_terms: list[str]
    word_count: int
    reading_time_min: int
    web_sources: list[dict] = []
    serp: dict | None = None


class AnalyzeResponse(BaseModel):
    score: int
    breakdown: dict
    suggestions: list[str]
    details: dict


class OptimizeResponse(BaseModel):
    optimized_article: str
    changelog: list[str]
    seo_before: int
    seo_after: int
    geo_before: int
    geo_after: int


class PublishResponse(BaseModel):
    ok: bool
    url: str = ""
    id: str | int | None = None
    error: str = ""
    preview: str = ""
