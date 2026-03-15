import type {
  AnalyzeResponse,
  ConfigData,
  GenerateRequest,
  GenerateResponse,
  OptimizeResponse,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof error.detail === "string" ? error.detail : "Request failed");
  }

  return response.json();
}

export const api = {
  getConfig: () => request<ConfigData>("/api/v1/config/all"),
  generate: (payload: GenerateRequest) =>
    request<GenerateResponse>("/api/v1/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  analyzeSeo: (article: string, keywords: string) =>
    request<AnalyzeResponse>("/api/v1/analyze/seo", {
      method: "POST",
      body: JSON.stringify({ article, keywords }),
    }),
  analyzeGeo: (article: string, keywords: string, faqPairs: Array<{ q: string; a: string }> = []) =>
    request<AnalyzeResponse>("/api/v1/analyze/geo", {
      method: "POST",
      body: JSON.stringify({ article, keywords, faq_pairs: faqPairs }),
    }),
  analyzeExternal: (article: string, keywords: string) =>
    request<{ seo: AnalyzeResponse["details"]; geo: AnalyzeResponse["details"] }>("/api/v1/external/analyze", {
      method: "POST",
      body: JSON.stringify({ article, keywords }),
    }),
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
    }),
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
    }),
};
