export interface Provider {
  id: string;
  label: string;
  base_url: string;
  models: string[];
  key_prefix: string;
  get_key_url: string;
  sdk?: string;
}

export interface ConfigData {
  providers: Provider[];
  scenario_categories: Record<string, Scenario[]>;
  article_styles: Record<string, { id: string; desc: string; instruction: string }>;
  keyword_presets: Array<{ label: string; keywords: string; difficulty: string }>;
  languages: Record<string, { code: string; instruction: string; direction: string }>;
  selling_point_groups: Record<string, Record<string, string>>;
}

export interface Scenario {
  label: string;
  audience_tag: string;
  keywords: string;
  selling_points: string[];
  style_hint: string;
  pixabay_terms?: string[];
}

export interface GenerateRequest {
  provider: string;
  model: string;
  api_key: string;
  base_url: string;
  language: string;
  category: string;
  scenario: string;
  style: string;
  keywords: string;
  selling_points: string[];
  include_images: boolean;
  image_count: number;
  use_web: boolean;
  use_serp: boolean;
  geo_mode: boolean;
  word_count_target?: number;
  target_title?: string;
}

export interface GenerateResponse {
  title: string;
  meta_description: string;
  slug: string;
  ab_titles: string[];
  article: string;
  faq_pairs: Array<{ q: string; a: string }>;
  images: Array<{ url: string; alt_text?: string; photographer?: string; source?: string }>;
  image_prompts: Array<{ scene: string; prompt: string }>;
  image_search_terms: string[];
  word_count: number;
  reading_time_min: number;
  web_sources?: Array<{ url: string; title?: string }>;
  serp?: Record<string, unknown> | null;
}

export interface AnalyzeResponse {
  score: number;
  breakdown: Record<string, unknown>;
  suggestions: string[];
  details: Record<string, unknown>;
}

export interface OptimizeResponse {
  optimized_article: string;
  changelog: string[];
  seo_before: number;
  seo_after: number;
  geo_before: number;
  geo_after: number;
}

export interface HistoryItem {
  id: string;
  createdAt: string;
  scenario: string;
  keywords: string;
  result: GenerateResponse;
  seoScore: number;
  geoScore: number;
}

export interface AiDetectResult {
  score: number;
  traces: string[];
  high_risk_paragraphs: string[];
  summary: string;
}

export interface PublishPayload {
  title: string;
  article: string;
  meta_description?: string;
  slug?: string;
  tags?: string[];
  canonical_url?: string;
  published?: boolean;
  api_key?: string;
  token?: string;
  publication_id?: string;
  medium_token?: string;
  paragraph_key?: string;
}

export interface PublishResponse {
  ok?: boolean;
  preview?: string;
  url?: string;
  id?: string | number;
  [key: string]: unknown;
}

export interface TranslateRequest {
  provider: string;
  model: string;
  api_key: string;
  base_url: string;
  article: string;
  source_lang: string;
  target_lang: string;
}

export interface TranslateResponse {
  translated_article: string;
  source_lang: string;
  target_lang: string;
}

export interface TopicSuggestion {
  title: string;
  search_intent: string;
  difficulty: string;
  keywords: string[];
}

export interface IdeationRequest {
  provider: string;
  model: string;
  api_key: string;
  base_url: string;
  core_keyword: string;
  industry?: string;
  count?: number;
  language?: string;
}

export interface IdeationResponse {
  topics: TopicSuggestion[];
  core_keyword: string;
  count: number;
}

export interface QAPair {
  question: string;
  answer: string;
  category: string;
}

export interface IntercomQARequest {
  provider: string;
  model: string;
  api_key: string;
  base_url: string;
  feature_description: string;
  product_name?: string;
  tone?: string;
  count?: number;
  languages?: string[];
}

export interface IntercomQAResponse {
  qa_by_language: Record<string, QAPair[]>;
  languages: string[];
  count_per_language: Record<string, number>;
}

export interface IntercomUploadRequest {
  intercom_token: string;
  collection_id?: string;
  title: string;
  body: string;
  state?: string;
  locale?: string;
}

export interface IntercomUploadResponse {
  ok: boolean;
  article_id: string;
  url: string;
}

export interface IntercomCollection {
  id: string;
  name: string;
  translated_content: Record<string, string>;
}

export interface IntercomCollectionsResponse {
  collections: IntercomCollection[];
  count: number;
}
