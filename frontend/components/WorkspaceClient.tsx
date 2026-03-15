"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { pushHistory } from "@/lib/history";
import type { AnalyzeResponse, ConfigData, GenerateRequest, GenerateResponse, Scenario } from "@/lib/types";

const EMPTY_FORM: GenerateRequest = {
  provider: "openai",
  model: "gpt-4o",
  api_key: "",
  base_url: "",
  language: "",
  category: "",
  scenario: "",
  style: "",
  keywords: "",
  selling_points: [],
  include_images: true,
  image_count: 3,
  use_web: false,
  use_serp: false,
  geo_mode: true,
};

export function WorkspaceClient() {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [form, setForm] = useState<GenerateRequest>(EMPTY_FORM);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [seo, setSeo] = useState<AnalyzeResponse | null>(null);
  const [geo, setGeo] = useState<AnalyzeResponse | null>(null);
  const [changelog, setChangelog] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getConfig()
      .then((data) => {
        setConfig(data);
        const category = Object.keys(data.scenario_categories)[0] || "";
        const firstScenario = data.scenario_categories[category]?.[0];
        const firstProvider = data.providers[0];
        const firstStyle = Object.keys(data.article_styles)[0] || "";
        const firstLanguage = Object.keys(data.languages)[0] || "";
        setForm((prev) => ({
          ...prev,
          provider: firstProvider?.id || prev.provider,
          model: firstProvider?.models?.[0] || prev.model,
          base_url: firstProvider?.base_url || prev.base_url,
          language: firstLanguage,
          category,
          scenario: firstScenario?.label || "",
          style: firstStyle,
          keywords: firstScenario?.keywords || "",
          selling_points: firstScenario?.selling_points || [],
        }));
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const selectedProvider = useMemo(
    () => config?.providers.find((item) => item.id === form.provider),
    [config, form.provider],
  );

  const scenarios = useMemo(
    () => (config ? config.scenario_categories[form.category] || [] : []),
    [config, form.category],
  );

  const selectedScenario = useMemo(
    () => scenarios.find((item) => item.label === form.scenario),
    [scenarios, form.scenario],
  );

  function updateForm<K extends keyof GenerateRequest>(key: K, value: GenerateRequest[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function handleCategoryChange(category: string) {
    const nextScenario = config?.scenario_categories[category]?.[0];
    setForm((prev) => ({
      ...prev,
      category,
      scenario: nextScenario?.label || "",
      keywords: nextScenario?.keywords || "",
      selling_points: nextScenario?.selling_points || [],
    }));
  }

  function handleScenarioChange(label: string) {
    const nextScenario = scenarios.find((item) => item.label === label);
    setForm((prev) => ({
      ...prev,
      scenario: label,
      keywords: nextScenario?.keywords || prev.keywords,
      selling_points: nextScenario?.selling_points || prev.selling_points,
    }));
  }

  function handleProviderChange(providerId: string) {
    const nextProvider = config?.providers.find((item) => item.id === providerId);
    setForm((prev) => ({
      ...prev,
      provider: providerId,
      model: nextProvider?.models?.[0] || prev.model,
      base_url: nextProvider?.base_url || prev.base_url,
    }));
  }

  async function runAnalyses(nextResult: GenerateResponse, keywords: string) {
    const [seoResponse, geoResponse] = await Promise.all([
      api.analyzeSeo(nextResult.article, keywords),
      api.analyzeGeo(nextResult.article, keywords, nextResult.faq_pairs),
    ]);
    setSeo(seoResponse);
    setGeo(geoResponse);
    pushHistory({
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      scenario: form.scenario,
      keywords,
      result: nextResult,
      seoScore: seoResponse.score,
      geoScore: geoResponse.score,
    });
  }

  async function handleGenerate() {
    try {
      setIsLoading(true);
      setError("");
      setChangelog([]);
      const generated = await api.generate(form);
      setResult(generated);
      await runAnalyses(generated, form.keywords);
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleOptimize(mode: "seo" | "geo" | "dual" | "triple") {
    if (!result) return;
    try {
      setIsLoading(true);
      setError("");
      const optimized = await api.optimize({
        provider: form.provider,
        api_key: form.api_key,
        model: form.model,
        base_url: form.base_url,
        article: result.article,
        keywords: form.keywords,
        mode,
      });
      const nextResult = { ...result, article: optimized.optimized_article };
      setResult(nextResult);
      setChangelog(optimized.changelog);
      await runAnalyses(nextResult, form.keywords);
    } catch (err) {
      setError(err instanceof Error ? err.message : "优化失败");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="page-shell">
      <section className="hero-card">
        <div>
          <span className="eyebrow">MPChat v5</span>
          <h1>Apple HIG 风格的内容工作台</h1>
          <p>按文档落地的 Next.js + FastAPI 产品形态，保留生成、分析、优化与分发主流程。</p>
        </div>
        <div className="hero-stats">
          <div className="metric-card">
            <span>场景数</span>
            <strong>{config ? Object.values(config.scenario_categories).flat().length : "--"}</strong>
          </div>
          <div className="metric-card">
            <span>状态</span>
            <strong>{isLoading ? "生成中" : "可用"}</strong>
          </div>
        </div>
      </section>

      <section className="glass-card">
        <div className="section-header">
          <div>
            <h2>创作配置</h2>
            <p>从服务商、场景、文风到 SERP/GEO 开关一次配置完成。</p>
          </div>
          <button className="primary-button" onClick={handleGenerate} disabled={isLoading || !config}>
            {isLoading ? "处理中..." : "生成文章"}
          </button>
        </div>

        <div className="form-grid">
          <label>
            <span>Provider</span>
            <select value={form.provider} onChange={(e) => handleProviderChange(e.target.value)}>
              {config?.providers.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Model</span>
            <select value={form.model} onChange={(e) => updateForm("model", e.target.value)}>
              {(selectedProvider?.models || [form.model]).map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Language</span>
            <select value={form.language} onChange={(e) => updateForm("language", e.target.value)}>
              {Object.keys(config?.languages || {}).map((language) => (
                <option key={language} value={language}>
                  {language}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Category</span>
            <select value={form.category} onChange={(e) => handleCategoryChange(e.target.value)}>
              {Object.keys(config?.scenario_categories || {}).map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Scenario</span>
            <select value={form.scenario} onChange={(e) => handleScenarioChange(e.target.value)}>
              {scenarios.map((scenario) => (
                <option key={scenario.label} value={scenario.label}>
                  {scenario.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Style</span>
            <select value={form.style} onChange={(e) => updateForm("style", e.target.value)}>
              {Object.keys(config?.article_styles || {}).map((style) => (
                <option key={style} value={style}>
                  {style}
                </option>
              ))}
            </select>
          </label>
          <label className="span-2">
            <span>API Key</span>
            <input type="password" value={form.api_key} onChange={(e) => updateForm("api_key", e.target.value)} />
          </label>
          <label className="span-2">
            <span>Base URL</span>
            <input value={form.base_url} onChange={(e) => updateForm("base_url", e.target.value)} />
          </label>
          <label className="span-4">
            <span>Keywords</span>
            <textarea value={form.keywords} onChange={(e) => updateForm("keywords", e.target.value)} rows={3} />
          </label>
        </div>

        {selectedScenario && (
          <div className="pill-row">
            <span className="subtle-label">默认卖点</span>
            {(selectedScenario as Scenario).selling_points.map((item) => (
              <span className="pill" key={item}>
                {item}
              </span>
            ))}
          </div>
        )}

        <div className="toggle-row">
          <label className="toggle">
            <input type="checkbox" checked={form.include_images} onChange={(e) => updateForm("include_images", e.target.checked)} />
            <span>配图</span>
          </label>
          <label className="toggle">
            <input type="checkbox" checked={form.use_web} onChange={(e) => updateForm("use_web", e.target.checked)} />
            <span>网页知识库</span>
          </label>
          <label className="toggle">
            <input type="checkbox" checked={form.use_serp} onChange={(e) => updateForm("use_serp", e.target.checked)} />
            <span>SERP 分析</span>
          </label>
          <label className="toggle">
            <input type="checkbox" checked={form.geo_mode} onChange={(e) => updateForm("geo_mode", e.target.checked)} />
            <span>GEO 模式</span>
          </label>
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      {result ? (
        <>
          <section className="score-strip">
            <div className="score-card">
              <span>SEO</span>
              <strong>{seo?.score ?? "--"}</strong>
            </div>
            <div className="score-card">
              <span>GEO</span>
              <strong>{geo?.score ?? "--"}</strong>
            </div>
            <div className="action-row">
              <button className="secondary-button" onClick={() => handleOptimize("seo")} disabled={isLoading}>
                SEO 优化
              </button>
              <button className="secondary-button" onClick={() => handleOptimize("geo")} disabled={isLoading}>
                GEO 优化
              </button>
              <button className="secondary-button" onClick={() => handleOptimize("dual")} disabled={isLoading}>
                双优化
              </button>
              <button className="primary-button" onClick={() => handleOptimize("triple")} disabled={isLoading}>
                三合一优化
              </button>
            </div>
          </section>

          <section className="results-grid">
            <article className="glass-card">
              <div className="section-header">
                <div>
                  <h2>{result.title}</h2>
                  <p>{result.meta_description}</p>
                </div>
                <span className="slug-chip">/{result.slug}</span>
              </div>
              <div className="pill-row">
                {result.ab_titles.map((title) => (
                  <span className="pill" key={title}>
                    {title}
                  </span>
                ))}
              </div>
              <div className="article-card">{result.article}</div>
            </article>

            <aside className="stack-column">
              <div className="glass-card">
                <h3>文章画像</h3>
                <div className="mini-metrics">
                  <div>
                    <span>字数</span>
                    <strong>{result.word_count}</strong>
                  </div>
                  <div>
                    <span>阅读时间</span>
                    <strong>{result.reading_time_min} min</strong>
                  </div>
                </div>
                <h4>优化建议</h4>
                <ul className="plain-list">
                  {(seo?.suggestions || []).concat(geo?.suggestions || []).slice(0, 6).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="glass-card">
                <h3>图片与提示词</h3>
                <div className="image-grid">
                  {result.images.map((image) => (
                    <Image
                      key={image.url}
                      src={image.url}
                      alt={image.alt_text || result.title}
                      className="preview-image"
                      width={640}
                      height={480}
                      unoptimized
                    />
                  ))}
                </div>
                <ul className="plain-list">
                  {result.image_search_terms.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="glass-card">
                <h3>FAQ</h3>
                <ul className="plain-list">
                  {result.faq_pairs.map((item) => (
                    <li key={item.q}>
                      <strong>{item.q}</strong>
                      <p>{item.a}</p>
                    </li>
                  ))}
                </ul>
              </div>

              {changelog.length ? (
                <div className="glass-card">
                  <h3>本次优化改动</h3>
                  <ul className="plain-list">
                    {changelog.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </aside>
          </section>
        </>
      ) : null}
    </div>
  );
}
