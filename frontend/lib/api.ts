import type {
  AnalyzeResponse,
  ConfigData,
  GenerateRequest,
  GenerateResponse,
  IdeationRequest,
  IdeationResponse,
  IntercomCollection,
  IntercomCollectionsResponse,
  IntercomQARequest,
  IntercomQAResponse,
  IntercomUploadRequest,
  IntercomUploadResponse,
  OptimizeResponse,
  PublishPayload,
  PublishResponse,
  TranslateRequest,
  TranslateResponse,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

function parseError(body: unknown): string {
  if (!body || typeof body !== "object") return "Request failed";
  const obj = body as Record<string, unknown>;
  if (typeof obj.detail === "string") return obj.detail;
  if (Array.isArray(obj.detail)) {
    return obj.detail
      .map((item: Record<string, unknown>) => {
        const loc = item.loc as string[] | undefined;
        const field = loc?.slice(-1)[0] || "";
        const msg = (item.msg as string) || "validation error";
        return field ? `${field}: ${msg}` : msg;
      })
      .join("; ");
  }
  if (typeof obj.message === "string") return obj.message;
  return "Request failed";
}

async function request<T>(path: string, options?: RequestInit, timeoutMs = 120000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
        ...(options?.headers || {}),
      },
      ...options,
      signal: controller.signal,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(parseError(body));
    }
    return res.json();
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error("请求超时，请减少字数目标或关闭 SERP/网页知识库后重试");
    }
    if (e instanceof TypeError && (e.message === "Failed to fetch" || e.message.includes("network"))) {
      throw new Error("网络请求失败，后端可能正在冷启动中（约30秒），请稍后重试");
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  getConfig: () => request<ConfigData>("/api/v1/config/all"),

  generate: (payload: GenerateRequest) =>
    request<GenerateResponse>("/api/v1/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }, 180000),

  analyzeSeo: (article: string, keywords: string) =>
    request<AnalyzeResponse>("/api/v1/analyze/seo", {
      method: "POST",
      body: JSON.stringify({ article, keywords }),
    }),

  analyzeGeo: (
    article: string,
    keywords: string,
    faqPairs: Array<{ q: string; a: string }> = [],
  ) =>
    request<AnalyzeResponse>("/api/v1/analyze/geo", {
      method: "POST",
      body: JSON.stringify({ article, keywords, faq_pairs: faqPairs }),
    }),

  analyzeExternal: (article: string, keywords: string) =>
    request<{ seo: Record<string, unknown>; geo: Record<string, unknown> }>(
      "/api/v1/external/analyze",
      { method: "POST", body: JSON.stringify({ article, keywords }) },
    ),

  optimize: (payload: {
    api_key: string;
    model: string;
    base_url: string;
    article: string;
    keywords: string;
    mode: "seo" | "geo" | "dual" | "triple" | "humanize";
    provider?: string;
  }) =>
    request<OptimizeResponse>("/api/v1/optimize", {
      method: "POST",
      body: JSON.stringify(payload),
    }, 180000),

  optimizeExternal: (payload: {
    api_key: string;
    model: string;
    base_url: string;
    article: string;
    keywords: string;
    mode: "seo" | "geo" | "dual" | "triple" | "humanize";
    provider?: string;
  }) =>
    request<OptimizeResponse>("/api/v1/external/optimize", {
      method: "POST",
      body: JSON.stringify(payload),
    }, 180000),

  detectAi: (payload: {
    api_key: string;
    model: string;
    base_url: string;
    article: string;
    provider?: string;
  }) =>
    request<{ result: unknown }>("/api/v1/detect/ai", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getSchema: (payload: {
    title: string;
    description?: string;
    author?: string;
    date?: string;
    image_url?: string;
    article_url?: string;
    faq_pairs?: Array<{ q: string; a: string }>;
  }) =>
    request<{
      article_schema: Record<string, unknown>;
      faq_schema: Record<string, unknown>;
    }>("/api/v1/schema", { method: "POST", body: JSON.stringify(payload) }),

  getInternalLinks: (sellingPoints: string[]) =>
    request<{ links: Array<{ text: string; url: string }> }>("/api/v1/links", {
      method: "POST",
      body: JSON.stringify({ selling_points: sellingPoints }),
    }),

  analyzeSerp: (keyword: string) =>
    request<Record<string, unknown>>("/api/v1/serp/analyze", {
      method: "POST",
      body: JSON.stringify({ keyword }),
    }),

  publishTo: (platform: string, payload: PublishPayload) =>
    request<PublishResponse>(`/api/v1/publish/${platform}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  translate: (payload: TranslateRequest) =>
    request<TranslateResponse>("/api/v1/translate", {
      method: "POST",
      body: JSON.stringify(payload),
    }, 120000),

  translateExternal: (payload: TranslateRequest) =>
    request<TranslateResponse>("/api/v1/external/translate", {
      method: "POST",
      body: JSON.stringify(payload),
    }, 120000),

  generateTopics: (payload: IdeationRequest) =>
    request<IdeationResponse>("/api/v1/ideation/topics", {
      method: "POST",
      body: JSON.stringify(payload),
    }, 120000),

  generateIntercomQA: (payload: IntercomQARequest) =>
    request<IntercomQAResponse>("/api/v1/intercom/generate-qa", {
      method: "POST",
      body: JSON.stringify(payload),
    }, 120000),

  uploadToIntercom: (payload: IntercomUploadRequest) =>
    request<IntercomUploadResponse>("/api/v1/intercom/upload", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getIntercomCollections: (token: string): Promise<IntercomCollectionsResponse> => {
    const params = new URLSearchParams({ token });
    return request<IntercomCollectionsResponse>(`/api/v1/intercom/collections?${params}`);
  },
};
