"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { loadAiConfig, saveAiConfig, type AiConfig } from "@/lib/aiConfig";
import { FALLBACK_CONFIG } from "@/lib/fallbackConfig";
import type { Provider, TopicSuggestion } from "@/lib/types";

const LLM_REGION_ERR_KEY = "err.llmRegionNotSupported";
const IDEATION_PREFILL_KEY = "mpchat-ideation-prefill";
const IDEATION_TOPICS_CACHE_KEY = "mpchat-ideation-topics";

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "var(--success)",
  medium: "var(--warning)",
  hard: "var(--danger)",
};

const INTENT_LABELS: Record<string, string> = {
  informational: "信息型",
  commercial: "商业型",
  transactional: "交易型",
  navigational: "导航型",
};

const LANGUAGE_OPTIONS = [
  { value: "auto", labelZh: "自动（跟随关键词语言）" },
  { value: "zh", labelZh: "中文" },
  { value: "en", labelZh: "英文" },
];

export function IdeationClient() {
  const { t } = useI18n();
  const router = useRouter();
  const DEFAULT_GEMINI_KEY = process.env.NEXT_PUBLIC_DEFAULT_GEMINI_KEY || "";
  const DEFAULT_KIMI_KEY = process.env.NEXT_PUBLIC_DEFAULT_KIMI_KEY || "";

  // 从后端 config 加载 providers（与工作台同源）
  const [providers, setProviders] = useState<Provider[]>(FALLBACK_CONFIG.providers);

  const [aiCfg, setAiCfg] = useState<AiConfig>({
    provider: "kimi",
    model: "kimi-k2.5",
    api_key: DEFAULT_KIMI_KEY,
    base_url: "https://api.moonshot.cn/v1",
  });
  const [configExpanded, setConfigExpanded] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [coreKeyword, setCoreKeyword] = useState("");
  const [industry, setIndustry] = useState("");
  const [count, setCount] = useState(20);
  const [language, setLanguage] = useState("auto");
  const [topics, setTopics] = useState<TopicSuggestion[]>([]);
  const [cachedKeyword, setCachedKeyword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [adoptedTitle, setAdoptedTitle] = useState("");
  const [showWarmup, setShowWarmup] = useState(false);

  // 加载后端 providers + localStorage 恢复 AI 配置 + topics 缓存
  useEffect(() => {
    api.getConfig().then((data) => {
      if (data.providers?.length) setProviders(data.providers);
    }).catch(() => { /* 保持 fallback */ });

    const saved = loadAiConfig();
    if (saved && saved.api_key) setAiCfg(saved);

    try {
      const cache = window.localStorage.getItem(IDEATION_TOPICS_CACHE_KEY);
      if (cache) {
        const { topics: cachedTopics, keyword } = JSON.parse(cache);
        if (Array.isArray(cachedTopics) && cachedTopics.length > 0) {
          setTopics(cachedTopics);
          setCachedKeyword(keyword || "");
        }
      }
    } catch { /* noop */ }
  }, []);

  // topics 变化时同步到 localStorage
  useEffect(() => {
    if (topics.length > 0) {
      try {
        window.localStorage.setItem(
          IDEATION_TOPICS_CACHE_KEY,
          JSON.stringify({ topics, keyword: coreKeyword }),
        );
      } catch { /* noop */ }
    }
  }, [topics, coreKeyword]);

  useEffect(() => {
    if (!error) return;
    const timer = setTimeout(() => setError(""), 8000);
    return () => clearTimeout(timer);
  }, [error]);

  useEffect(() => {
    if (aiCfg.provider && aiCfg.api_key) saveAiConfig(aiCfg);
  }, [aiCfg.provider, aiCfg.model, aiCfg.api_key, aiCfg.base_url]);

  const currentProvider = useMemo(
    () => providers.find((p) => p.id === aiCfg.provider),
    [providers, aiCfg.provider],
  );

  function handleProviderChange(providerId: string) {
    const p = providers.find((x) => x.id === providerId);
    const newKey = providerId === "gemini" ? DEFAULT_GEMINI_KEY : providerId === "kimi" ? DEFAULT_KIMI_KEY : "";
    setAiCfg((prev) => ({
      ...prev,
      provider: providerId,
      model: p?.models?.[0] || "",
      base_url: p?.base_url || "",
      api_key: newKey || prev.api_key,
    }));
  }

  async function handleGenerate() {
    if (!coreKeyword.trim()) {
      setError(t("err.ideation.noKeyword"));
      return;
    }
    if (!aiCfg.api_key.trim()) {
      setError(t("err.invalidKey"));
      return;
    }
    const warmupTimer = setTimeout(() => setShowWarmup(true), 8000);
    try {
      setIsLoading(true);
      setError("");
      setTopics([]);
      const resp = await api.generateTopics({
        provider: aiCfg.provider,
        api_key: aiCfg.api_key,
        base_url: aiCfg.base_url,
        model: aiCfg.model,
        core_keyword: coreKeyword.trim(),
        industry: industry.trim(),
        count,
        language,
      });
      setTopics(resp.topics);
      if (resp.topics.length === 0) {
        setError(t("msg.ideation.noTopics"));
      }
    } catch (e) {
      const raw = e instanceof Error ? e.message : t("err.requestFailed");
      setError(raw === LLM_REGION_ERR_KEY ? t(LLM_REGION_ERR_KEY) : raw);
    } finally {
      clearTimeout(warmupTimer);
      setShowWarmup(false);
      setIsLoading(false);
    }
  }

  function handleUseTitle(topic: TopicSuggestion) {
    const keywords = topic.keywords.join(", ");
    window.localStorage.setItem(
      IDEATION_PREFILL_KEY,
      JSON.stringify({ keywords, title: topic.title }),
    );
    setAdoptedTitle(topic.title);
    router.push("/");
  }

  const modelOptions = currentProvider?.models ?? [];

  return (
    <div className="workspace-layout" style={{ maxWidth: 900, margin: "0 auto" }}>
      {/* ── 配置面板 ── */}
      <section className="glass-card">
        <div className="section-header" style={{ marginBottom: configExpanded ? 16 : 0 }}>
          <h2 style={{ margin: 0 }}>{t("ideation.title")}</h2>
          <button className="secondary-button" onClick={() => setConfigExpanded((v) => !v)} style={{ padding: "4px 12px", fontSize: "0.82rem" }}>
            {t("aiConfig.title")} {configExpanded ? "▲" : "▼"}
          </button>
        </div>

        {configExpanded && (
          <div className="form-grid" style={{ marginBottom: 0 }}>
            <label>
              <span>{t("form.provider")}</span>
              <select value={aiCfg.provider} onChange={(e) => handleProviderChange(e.target.value)}>
                {providers.map((p) => (
                  <option key={p.id} value={p.id}>{p.label}</option>
                ))}
              </select>
            </label>

            <label>
              <span>{t("form.model")}</span>
              {modelOptions.length > 0 ? (
                <select value={aiCfg.model} onChange={(e) => setAiCfg((c) => ({ ...c, model: e.target.value }))}>
                  {modelOptions.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              ) : (
                <input
                  value={aiCfg.model}
                  onChange={(e) => setAiCfg((c) => ({ ...c, model: e.target.value }))}
                  placeholder="输入模型名称（如 gemini-3.1-pro）"
                />
              )}
            </label>

            <label>
              <span>
                {t("form.apiKey")}
                {currentProvider?.get_key_url && (
                  <a
                    href={currentProvider.get_key_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: "var(--primary)", fontSize: "0.75rem", marginLeft: 6 }}
                  >
                    获取
                  </a>
                )}
              </span>
              <div style={{ position: "relative" }}>
                <input
                  type={showApiKey ? "text" : "password"}
                  value={aiCfg.api_key}
                  onChange={(e) => setAiCfg((c) => ({ ...c, api_key: e.target.value }))}
                  style={{ paddingRight: 40 }}
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey((v) => !v)}
                  style={{ position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "var(--muted)", fontSize: "0.85rem", padding: 0 }}
                  title={showApiKey ? "隐藏" : "查看"}
                >
                  {showApiKey ? "🙈" : "👁"}
                </button>
              </div>
            </label>

            <label>
              <span>{t("form.baseUrl")}</span>
              <input value={aiCfg.base_url} onChange={(e) => setAiCfg((c) => ({ ...c, base_url: e.target.value }))} />
            </label>
          </div>
        )}
      </section>

      {/* ── 输入面板 ── */}
      <section className="glass-card">
        <h2>{t("ideation.inputTitle")}</h2>
        <div className="form-grid">
          <label className="span-4">
            <span>{t("ideation.coreKeyword")}</span>
            <input
              placeholder={t("ideation.coreKeywordPlaceholder")}
              value={coreKeyword}
              onChange={(e) => setCoreKeyword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
            />
          </label>
          <label className="span-2">
            <span>{t("ideation.industry")}</span>
            <input
              placeholder={t("ideation.industryPlaceholder")}
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
            />
          </label>
          <label className="span-2">
            <span>{t("ideation.titleLanguage")}</span>
            <select value={language} onChange={(e) => setLanguage(e.target.value)}>
              {LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.labelZh}</option>
              ))}
            </select>
          </label>
          <label className="span-4">
            <span>{t("ideation.count")} — {count}</span>
            <input type="range" min={5} max={50} step={5} value={count} onChange={(e) => setCount(Number(e.target.value))} style={{ width: "100%", marginTop: 6 }} />
          </label>
        </div>

        <div className="action-row" style={{ marginTop: 16 }}>
          <button className="primary-button" onClick={handleGenerate} disabled={isLoading}>
            {isLoading ? t("ideation.generating") : t("ideation.generate")}
          </button>
          {topics.length > 0 && (
            <span className="muted-text" style={{ fontSize: "0.85rem" }}>
              {t("ideation.resultCount").replace("{n}", String(topics.length))}
              {cachedKeyword && cachedKeyword !== coreKeyword && (
                <span style={{ marginLeft: 8, opacity: 0.6 }}>
                  ({t("ideation.cachedFor")}: {cachedKeyword})
                </span>
              )}
            </span>
          )}
        </div>

        {showWarmup && (
          <p className="muted-text" style={{ marginTop: 8, fontSize: "0.82rem" }}>{t("msg.serverWarmup")}</p>
        )}
        {error && (
          <p style={{ color: "var(--danger)", marginTop: 8, fontSize: "0.85rem" }}>{error}</p>
        )}
        {adoptedTitle && (
          <p style={{ color: "var(--success)", marginTop: 8, fontSize: "0.85rem" }}>
            {t("ideation.adopted")}: <strong>{adoptedTitle}</strong>
          </p>
        )}
      </section>

      {/* ── 结果列表 ── */}
      {topics.length > 0 && (
        <section className="glass-card">
          <h2>{t("ideation.results")}</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {topics.map((topic, i) => (
              <div key={i} className="article-card" style={{ padding: "14px 16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
                  <div style={{ flex: 1 }}>
                    <p style={{ margin: "0 0 8px", fontWeight: 600, lineHeight: 1.4 }}>{topic.title}</p>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                      <span style={{ fontSize: "0.75rem", padding: "2px 8px", borderRadius: 4, background: "rgba(255,255,255,0.08)", color: "var(--muted)" }}>
                        {INTENT_LABELS[topic.search_intent] || topic.search_intent}
                      </span>
                      <span style={{ fontSize: "0.75rem", padding: "2px 8px", borderRadius: 4, background: "rgba(255,255,255,0.06)", color: DIFFICULTY_COLORS[topic.difficulty] || "var(--muted)" }}>
                        {t(`ideation.difficulty.${topic.difficulty}`) || topic.difficulty}
                      </span>
                      {topic.keywords.slice(0, 4).map((kw) => (
                        <span key={kw} style={{ fontSize: "0.72rem", padding: "2px 7px", borderRadius: 4, background: "rgba(99,91,255,0.12)", color: "var(--primary)" }}>
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                  <button
                    className="secondary-button"
                    onClick={() => handleUseTitle(topic)}
                    style={{ flexShrink: 0, padding: "6px 14px", fontSize: "0.82rem" }}
                  >
                    {t("ideation.useTitle")}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
