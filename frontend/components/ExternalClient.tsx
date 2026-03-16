"use client";

import { useState, useEffect, useMemo } from "react";

import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { loadAiConfig, saveAiConfig, type AiConfig } from "@/lib/aiConfig";

const PROVIDER_DEFAULTS: Record<string, { model: string; base_url: string }> = {
  gemini: { model: "gemini-2.5-flash", base_url: "https://generativelanguage.googleapis.com/v1beta/openai/" },
  openai: { model: "gpt-4o", base_url: "https://api.openai.com/v1" },
  anthropic: { model: "claude-sonnet-4-20250514", base_url: "https://api.anthropic.com" },
  deepseek: { model: "deepseek-chat", base_url: "https://api.deepseek.com/v1" },
  kimi: { model: "moonshot-v1-128k", base_url: "https://api.moonshot.cn/v1" },
  groq: { model: "llama-3.3-70b-versatile", base_url: "https://api.groq.com/openai/v1" },
  together: { model: "meta-llama/Llama-3.3-70B-Instruct-Turbo", base_url: "https://api.together.xyz/v1" },
  siliconflow: { model: "Qwen/Qwen2.5-72B-Instruct", base_url: "https://api.siliconflow.cn/v1" },
  zhipu: { model: "glm-4-plus", base_url: "https://open.bigmodel.cn/api/paas/v4" },
  openrouter: { model: "anthropic/claude-sonnet-4", base_url: "https://openrouter.ai/api/v1" },
  custom: { model: "", base_url: "" },
};
import { ScoreRing } from "@/components/ScoreRing";
import type { AiDetectResult, OptimizeResponse } from "@/lib/types";

type ScoreBlock = {
  structure_score?: number;
  score?: number;
  issues?: string[];
  tips?: string[];
};

function downloadFile(content: string, filename: string, mime = "text/plain") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}



export function ExternalClient() {
  const { t } = useI18n();
  const DEFAULT_GEMINI_KEY = process.env.NEXT_PUBLIC_DEFAULT_GEMINI_KEY || "";
  const [article, setArticle] = useState("");
  const [keywords, setKeywords] = useState("");
  const [aiCfg, setAiCfg] = useState<AiConfig>({
    provider: "gemini",
    model: "gemini-2.5-flash",
    api_key: DEFAULT_GEMINI_KEY,
    base_url: "https://generativelanguage.googleapis.com/v1beta/openai/",
  });
  const [configExpanded, setConfigExpanded] = useState(false);
  const [showWarmup, setShowWarmup] = useState(false);
  const [analysis, setAnalysis] = useState<{ seo: ScoreBlock; geo: ScoreBlock } | null>(null);
  const [optimized, setOptimized] = useState<OptimizeResponse | null>(null);
  const [error, setError] = useState("");
  const [copyMsg, setCopyMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [originalArticle, setOriginalArticle] = useState("");
  const [showDiff, setShowDiff] = useState(false);
  const [aiDetect, setAiDetect] = useState<AiDetectResult | null>(null);

  useEffect(() => {
    const saved = loadAiConfig();
    if (saved && saved.api_key) setAiCfg(saved);
  }, []);

  useEffect(() => {
    if (!error) return;
    const t = setTimeout(() => setError(""), 8000);
    return () => clearTimeout(t);
  }, [error]);

  useEffect(() => {
    if (!copyMsg) return;
    const t = setTimeout(() => setCopyMsg(""), 2000);
    return () => clearTimeout(t);
  }, [copyMsg]);

  const configLabel = useMemo(() => {
    const providerNames: Record<string, string> = {
      gemini: "Google Gemini", openai: "OpenAI", anthropic: "Anthropic", deepseek: "DeepSeek",
      kimi: "Kimi", groq: "Groq", together: "Together AI", siliconflow: "SiliconFlow",
      zhipu: "Zhipu AI", openrouter: "OpenRouter", custom: "Custom",
    };
    return providerNames[aiCfg.provider] || aiCfg.provider;
  }, [aiCfg.provider]);

  async function handleAnalyze() {
    try {
      setLoading(true);
      setError("");
      const data = await api.analyzeExternal(article, keywords);
      setAnalysis(data as unknown as { seo: ScoreBlock; geo: ScoreBlock });
    } catch (err) {
      setError(err instanceof Error ? err.message : "分析失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleOptimize(mode: "seo" | "geo" | "dual" | "triple" | "humanize") {
    try {
      setLoading(true);
      setError("");
      if (!originalArticle) setOriginalArticle(article);
      const data = await api.optimizeExternal({
        provider: aiCfg.provider,
        api_key: aiCfg.api_key,
        model: aiCfg.model,
        base_url: aiCfg.base_url,
        article,
        keywords,
        mode,
      });
      setOptimized(data);
      setArticle(data.optimized_article);
      try {
        const refreshed = await api.analyzeExternal(data.optimized_article, keywords);
        setAnalysis(refreshed as unknown as { seo: ScoreBlock; geo: ScoreBlock });
      } catch {
        setError("优化成功，但分析刷新失败，请手动点击分析");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "优化失败");
    } finally {
      setLoading(false);
    }
  }

  function handleUndo() {
    if (originalArticle) {
      setArticle(originalArticle);
      setOriginalArticle("");
      setOptimized(null);
      setShowDiff(false);
    }
  }

  function parseAiDetectResult(raw: unknown): AiDetectResult {
    if (raw == null) return { score: 0, traces: [], high_risk_paragraphs: [], summary: "" };
    if (raw && typeof raw === "object" && "score" in raw) return raw as AiDetectResult;
    const text = typeof raw === "string" ? raw : JSON.stringify(raw);
    let score = 0;
    const scoreMatch = text.match(/(?:AI\s*评分|score)[：:]\s*(\d+)/i);
    if (scoreMatch) score = parseInt(scoreMatch[1], 10) / 100;
    const traces: string[] = [];
    const traceMatches = text.match(/\*\s+\*\*([^*]+)\*\*/g);
    if (traceMatches) traceMatches.forEach((m) => traces.push(m.replace(/\*+/g, "").trim()));
    return { score, traces, high_risk_paragraphs: [], summary: text };
  }

  async function handleDetectAi() {
    try {
      setLoading(true);
      setError("");
      const resp = await api.detectAi({
        api_key: aiCfg.api_key,
        model: aiCfg.model,
        base_url: aiCfg.base_url,
        article,
        provider: aiCfg.provider,
      });
      setAiDetect(parseAiDetectResult(resp.result));
    } catch (err) {
      setError(err instanceof Error ? err.message : "检测失败");
    } finally {
      setLoading(false);
    }
  }


  function doCopy(text: string) {
    navigator.clipboard.writeText(text).then(() => setCopyMsg("已复制")).catch(() => setCopyMsg("复制失败"));
  }

  return (
    <div className="page-shell">
      <section className="hero-card compact">
        <div>
          <span className="eyebrow">{t("nav.external")}</span>
          <h1>{t("nav.external")}</h1>
        </div>
      </section>

      <div className="ai-config-bar">
        <span>{t("aiConfig.title")}：{configLabel} / {aiCfg.model}</span>
        {aiCfg.api_key && <span className="config-status">✓</span>}
        <span className="config-modify" onClick={() => setConfigExpanded(!configExpanded)}>
          {configExpanded ? t("btn.collapse") : t("btn.modify")}
        </span>
      </div>

      {configExpanded && (
        <section className="glass-card" style={{marginBottom:16}}>
          <div className="form-grid">
            <label className="span-2">
              <span>{t("form.provider")}</span>
              <select value={aiCfg.provider} onChange={(e) => {
                  const id = e.target.value;
                  const defaults = PROVIDER_DEFAULTS[id] || { model: "", base_url: "" };
                  const newKey = id === "gemini" ? DEFAULT_GEMINI_KEY : "";
                  const newCfg = { provider: id, model: defaults.model, base_url: defaults.base_url, api_key: newKey };
                  setAiCfg(newCfg);
                  saveAiConfig(newCfg);
                }}>
                {[
                  { id: "gemini", label: "Google Gemini" },
                  { id: "openai", label: "OpenAI" },
                  { id: "anthropic", label: "Anthropic (Claude)" },
                  { id: "deepseek", label: "DeepSeek" },
                  { id: "kimi", label: "Kimi" },
                  { id: "groq", label: "Groq" },
                  { id: "together", label: "Together AI" },
                  { id: "siliconflow", label: "SiliconFlow" },
                  { id: "zhipu", label: "Zhipu AI" },
                  { id: "openrouter", label: "OpenRouter" },
                  { id: "custom", label: "Custom" },
                ].map((p) => (
                  <option key={p.id} value={p.id}>{p.label}</option>
                ))}
              </select>
            </label>
            <label>
              <span>{t("form.model")}</span>
              <input value={aiCfg.model} onChange={(e) => setAiCfg((p) => ({ ...p, model: e.target.value }))} />
            </label>
            <label>
              <span>{t("form.apiKey")}</span>
              <input type="password" value={aiCfg.api_key} onChange={(e) => setAiCfg((p) => ({ ...p, api_key: e.target.value }))} />
            </label>
            <label className="span-4">
              <span>{t("form.baseUrl")}</span>
              <input value={aiCfg.base_url} onChange={(e) => setAiCfg((p) => ({ ...p, base_url: e.target.value }))} />
            </label>
          </div>
        </section>
      )}

      <section className="glass-card">
        <div className="form-grid">
          <label className="span-4">
            <span>{t("form.article")}</span>
            <textarea rows={16} value={article} onChange={(e) => setArticle(e.target.value)} />
          </label>
          <label className="span-4">
            <span>{t("form.targetKeywords")}</span>
            <textarea rows={3} value={keywords} onChange={(e) => setKeywords(e.target.value)} />
          </label>
        </div>

        <div className="action-row" style={{marginTop:12}}>
          <button className="primary-button" onClick={handleAnalyze} disabled={loading || !article.trim()}>
            {loading ? t("msg.analyzing") : t("btn.analyze")}
          </button>
          <button className="secondary-button" onClick={() => handleOptimize("seo")} disabled={loading || !aiCfg.api_key.trim()}>{t("btn.optimizeSeo")}</button>
          <button className="secondary-button" onClick={() => handleOptimize("geo")} disabled={loading || !aiCfg.api_key.trim()}>{t("btn.optimizeGeo")}</button>
          <button className="secondary-button" onClick={() => handleOptimize("dual")} disabled={loading || !aiCfg.api_key.trim()}>{t("btn.optimizeDual")}</button>
          <button className="primary-button" onClick={() => handleOptimize("triple")} disabled={loading || !aiCfg.api_key.trim()}>{t("btn.optimizeTriple")}</button>
          <button className="secondary-button" onClick={() => handleOptimize("humanize")} disabled={loading || !aiCfg.api_key.trim()}>{t("btn.humanize")}</button>
          <button className="secondary-button" onClick={handleDetectAi} disabled={loading || !aiCfg.api_key.trim()}>{t("btn.detectAi")}</button>
        </div>

        {showWarmup && <div className="warmup-banner">{t("msg.serverWarmup")}</div>}

        {(originalArticle || optimized) && (
          <div className="action-row" style={{marginTop:8}}>
            {originalArticle && (
              <button className="secondary-button" onClick={handleUndo} style={{borderColor:"var(--warning)"}}>撤销优化 (恢复原文)</button>
            )}
            {originalArticle && (
              <button className="secondary-button" onClick={() => setShowDiff(!showDiff)}>{showDiff ? "关闭对比" : "对比原文"}</button>
            )}
            <button className="secondary-button" onClick={() => downloadFile(article, "optimized-article.md", "text/markdown")}>下载 Markdown</button>
            <button className="secondary-button" onClick={() => doCopy(article)}>复制文章</button>
          </div>
        )}
      </section>

      {error ? <div className="error-banner toast-error" onClick={() => setError("")}><span>{error}</span><span style={{cursor:"pointer",marginLeft:12,opacity:0.6}}>✕</span></div> : null}
      {copyMsg && <div className="error-banner toast-error" style={{background:"rgba(34,197,94,0.15)",borderColor:"rgba(34,197,94,0.3)",color:"#4ade80"}}>{copyMsg}</div>}

      {showDiff && originalArticle && (
        <section className="glass-card">
          <h2>原文 vs 优化后</h2>
          <div className="diff-grid">
            <div>
              <h4 style={{color:"var(--danger)"}}>原文</h4>
              <pre className="article-card" style={{maxHeight:400,overflow:"auto"}}>{originalArticle}</pre>
            </div>
            <div>
              <h4 style={{color:"var(--success)"}}>优化后</h4>
              <pre className="article-card" style={{maxHeight:400,overflow:"auto"}}>{article}</pre>
            </div>
          </div>
        </section>
      )}

      {aiDetect && (
        <section className="glass-card">
          <h2>AI 检测结果</h2>
          <div className="score-strip" style={{marginBottom:16}}>
            <ScoreRing score={Math.round((1 - aiDetect.score) * 100)} label="人性化得分" size={100} />
            <div style={{flex:1}}><p className="muted-text">{aiDetect.summary}</p></div>
          </div>
          {(aiDetect.traces?.length ?? 0) > 0 && (
            <div style={{marginBottom:12}}><h4>AI 痕迹</h4><ul className="plain-list">{(aiDetect.traces ?? []).map((tr) => (<li key={tr} style={{color:"var(--warning)"}}>{tr}</li>))}</ul></div>
          )}
          {(aiDetect.high_risk_paragraphs?.length ?? 0) > 0 && (
            <div><h4>高风险段落</h4>{(aiDetect.high_risk_paragraphs ?? []).map((p, i) => (<pre key={i} className="article-card" style={{borderColor:"rgba(255,107,129,0.3)",marginBottom:8,fontSize:"0.85rem"}}>{p}</pre>))}</div>
          )}
        </section>
      )}

      {analysis ? (
        <section className="results-grid">
          <div className="glass-card">
            <h2>SEO 诊断</h2>
            <ScoreRing score={analysis.seo?.structure_score ?? 0} label="SEO" size={100} />
            <pre className="article-card" style={{marginTop:12}}>{JSON.stringify(analysis.seo, null, 2)}</pre>
          </div>
          <div className="glass-card">
            <h2>GEO 诊断</h2>
            <ScoreRing score={analysis.geo?.score ?? 0} label="GEO" size={100} />
            <pre className="article-card" style={{marginTop:12}}>{JSON.stringify(analysis.geo, null, 2)}</pre>
          </div>
        </section>
      ) : null}

      {optimized ? (
        <section className="glass-card">
          <h2>优化结果</h2>
          <div className="score-strip">
            <div className="score-card"><span>SEO</span><strong>{optimized.seo_before} → {optimized.seo_after}</strong></div>
            <div className="score-card"><span>GEO</span><strong>{optimized.geo_before} → {optimized.geo_after}</strong></div>
          </div>
          <ul className="plain-list" style={{marginTop:12}}>{(optimized.changelog ?? []).map((item) => (<li key={item}>{item}</li>))}</ul>
        </section>
      ) : null}
    </div>
  );
}
