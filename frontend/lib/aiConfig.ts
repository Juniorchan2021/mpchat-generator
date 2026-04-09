const STORAGE_KEY = "mpchat-ai-config";

export interface AiConfig {
  provider: string;
  model: string;
  api_key: string;
  base_url: string;
}

const DEFAULT_KEYS: Record<string, string> = {
  gemini: process.env.NEXT_PUBLIC_DEFAULT_GEMINI_KEY || "",
  kimi: process.env.NEXT_PUBLIC_DEFAULT_KIMI_KEY || "",
};

/** Return the built-in default API key for a provider (empty string if none). */
export function getDefaultKey(providerId: string): string {
  return DEFAULT_KEYS[providerId] ?? "";
}

export function loadAiConfig(): AiConfig | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const saved: AiConfig = JSON.parse(raw);
    const builtinKey = getDefaultKey(saved.provider);
    if (builtinKey) {
      saved.api_key = builtinKey;
    }
    return saved;
  } catch {
    return null;
  }
}

export function saveAiConfig(config: AiConfig): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
}
