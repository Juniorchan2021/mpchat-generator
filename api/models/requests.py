from typing import Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = Field(min_length=1)
    base_url: str = ""
    language: str
    category: str
    scenario: str
    style: str
    keywords: str
    selling_points: list[str] = []
    include_images: bool = True
    image_count: int = Field(default=3, ge=0, le=10)
    use_web: bool = False
    use_serp: bool = False
    geo_mode: bool = True
    word_count_target: int = 1200


class ArticleAnalyzeRequest(BaseModel):
    article: str = Field(min_length=1, max_length=100000)
    keywords: str = ""
    faq_pairs: list[dict] = []
    target_url: str = ""


class OptimizeRequest(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = Field(min_length=1)
    base_url: str = ""
    article: str = Field(min_length=1, max_length=100000)
    keywords: str = ""
    mode: Literal["seo", "geo", "dual", "triple", "humanize"] = "dual"


class ExternalAnalyzeRequest(BaseModel):
    article: str = Field(min_length=1, max_length=100000)
    keywords: str = ""


class PublishRequest(BaseModel):
    title: str = Field(min_length=1)
    article: str = Field(min_length=1, max_length=100000)
    meta_description: str = ""
    slug: str = ""
    tags: list[str] = []
    canonical_url: str = ""
    published: bool = False
    api_key: str = ""
    token: str = ""
    publication_id: str = ""


class SchemaRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    author: str = "MPChat"
    date: str | None = None
    image_url: str = ""
    article_url: str = ""
    faq_pairs: list[dict] = []


class SlugRequest(BaseModel):
    title: str = Field(min_length=1)


class LinksRequest(BaseModel):
    selling_points: list[str] = []


class AiDetectRequest(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = Field(min_length=1)
    base_url: str = ""
    article: str = Field(min_length=1, max_length=100000)


class SerpAnalyzeRequest(BaseModel):
    keyword: str = Field(min_length=1)


class ImageSearchRequest(BaseModel):
    pixabay_key: str = ""
    pexels_key: str = ""
    scenario_terms: list[str] = []
    ai_terms: list[str] = []
    article_title: str = ""
    per_query: int = Field(default=2, ge=1, le=10)
