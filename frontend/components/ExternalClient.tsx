"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import type { OptimizeResponse } from "@/lib/types";

type ScoreBlock = {
  structure_score?: number;
  score?: number;
  issues?: string[];
  tips?: string[];
};

export function ExternalClient() {
  const [article, setArticle] = useState("");
  const [keywords, setKeywords] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("gpt-4o");
  const [baseUrl, setBaseUrl] = useState("");
  const [analysis, setAnalysis] = useState<{ seo: ScoreBlock; geo: ScoreBlock } | null>(null);
  const [optimized, setOptimized] = useState<OptimizeResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleAnalyze() {
    try {
      setLoading(true);
      setError("");
      const data = await api.analyzeExternal(article, keywords);
      setAnalysis(data);
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
      const data = await api.optimizeExternal({
        provider: "openai",
        api_key: apiKey,
        model,
        base_url: baseUrl,
        article,
        keywords,
        mode,
      });
      setOptimized(data);
      setArticle(data.optimized_article);
      const refreshed = await api.analyzeExternal(data.optimized_article, keywords);
      setAnalysis(refreshed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "优化失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-shell">
      <section className="hero-card compact">
        <div>
          <span className="eyebrow">External Article</span>
          <h1>外部文章优化</h1>
          <p>粘贴已有文章，直接获取 SEO/GEO 诊断，并用原始大模型能力做联动优化。</p>
        </div>
      </section>

      <section className="glass-card">
        <div className="form-grid">
          <label className="span-4">
            <span>文章正文</span>
            <textarea rows={16} value={article} onChange={(e) => setArticle(e.target.value)} />
          </label>
          <label className="span-4">
            <span>关键词</span>
            <textarea rows={3} value={keywords} onChange={(e) => setKeywords(e.target.value)} />
          </label>
          <label className="span-2">
            <span>API Key</span>
            <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
          </label>
          <label>
            <span>Model</span>
            <input value={model} onChange={(e) => setModel(e.target.value)} />
          </label>
          <label>
            <span>Base URL</span>
            <input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
          </label>
        </div>

        <div className="action-row">
          <button className="primary-button" onClick={handleAnalyze} disabled={loading || !article.trim()}>
            {loading ? "处理中..." : "开始分析"}
          </button>
          <button className="secondary-button" onClick={() => handleOptimize("seo")} disabled={loading || !apiKey.trim()}>
            SEO 优化
          </button>
          <button className="secondary-button" onClick={() => handleOptimize("geo")} disabled={loading || !apiKey.trim()}>
            GEO 优化
          </button>
          <button className="secondary-button" onClick={() => handleOptimize("dual")} disabled={loading || !apiKey.trim()}>
            双优化
          </button>
          <button className="primary-button" onClick={() => handleOptimize("triple")} disabled={loading || !apiKey.trim()}>
            三合一优化
          </button>
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      {analysis ? (
        <section className="results-grid">
          <div className="glass-card">
            <h2>SEO 诊断</h2>
            <div className="score-card large">
              <span>SEO</span>
              <strong>{analysis.seo.structure_score ?? "--"}</strong>
            </div>
            <pre className="article-card">{JSON.stringify(analysis.seo, null, 2)}</pre>
          </div>
          <div className="glass-card">
            <h2>GEO 诊断</h2>
            <div className="score-card large">
              <span>GEO</span>
              <strong>{analysis.geo.score ?? "--"}</strong>
            </div>
            <pre className="article-card">{JSON.stringify(analysis.geo, null, 2)}</pre>
          </div>
        </section>
      ) : null}

      {optimized ? (
        <section className="glass-card">
          <h2>优化结果</h2>
          <div className="score-strip">
            <div className="score-card">
              <span>SEO</span>
              <strong>
                {optimized.seo_before} → {optimized.seo_after}
              </strong>
            </div>
            <div className="score-card">
              <span>GEO</span>
              <strong>
                {optimized.geo_before} → {optimized.geo_after}
              </strong>
            </div>
          </div>
          <ul className="plain-list">
            {optimized.changelog.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
