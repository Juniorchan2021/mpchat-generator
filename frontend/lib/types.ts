export interface Provider {
  id: string;
  label: string;
  base_url: string;
  models: string[];
  key_prefix: string;
  get_key_url: string;
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
