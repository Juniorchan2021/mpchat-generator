"use client";

import Image from "next/image";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { marked } from "marked";
import { useEffect, useMemo, useState, useCallback } from "react";

import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { saveAiConfig } from "@/lib/aiConfig";
import { FALLBACK_CONFIG } from "@/lib/fallbackConfig";
import { pushHistory } from "@/lib/history";
import { getTranslateTargets } from "@/lib/translateUtils";
import { ScoreRing, BreakdownBar } from "@/components/ScoreRing";
import type {
  AiDetectResult,
  AnalyzeResponse,
  ConfigData,
  GenerateRequest,
  GenerateResponse,
  PublishResponse,
  Scenario,
} from "@/lib/types";

type ResultTab = "article" | "seo-geo" | "export" | "publish" | "ai-detect";

const DEFAULT_GEMINI_KEY = process.env.NEXT_PUBLIC_DEFAULT_GEMINI_KEY || "";
const DEFAULT_KIMI_KEY = process.env.NEXT_PUBLIC_DEFAULT_KIMI_KEY || "";

const EMPTY_FORM: GenerateRequest = {
  provider: "kimi",
  model: "kimi-k2.5",
  api_key: DEFAULT_KIMI_KEY,
  base_url: "https://api.moonshot.cn/v1",
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

const PLATFORMS = [
  { id: "devto", label: "Dev.to", needsKey: true },
  { id: "hashnode", label: "Hashnode", needsKey: true },
  { id: "medium", label: "Medium", needsKey: true },
  { id: "paragraph", label: "Paragraph", needsKey: true },
  { id: "linkedin", label: "LinkedIn", needsKey: false },
  { id: "twitter", label: "Twitter", needsKey: false },
  { id: "zhihu", label: "知乎", needsKey: false },
  { id: "wechat", label: "微信公众号", needsKey: false },
  { id: "crypto", label: "加密博客", needsKey: false },
];

function downloadFile(content: string, filename: string, mime = "text/plain") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}



function copyText(text: string, setCopy: (m: string) => void) {
  navigator.clipboard.writeText(text).then(() => setCopy("已复制")).catch(() => setCopy("复制失败"));
}

function interleaveImages(markdown: string, images: Array<{ url: string; alt_text?: string; photographer?: string; source?: string }>): string {
  if (!images.length) return markdown;
  const sections = markdown.split(/\n(?=##\s)/);
  if (sections.length <= 1) return markdown;
  const result: string[] = [sections[0]];
  for (let i = 1; i < sections.length; i++) {
    const img = images[(i - 1) % images.length];
    if (img && i <= images.length) {
      const alt = img.alt_text || "article image";
      const credit = img.photographer ? ` *Photo: ${img.photographer} (${img.source || ""})*` : "";
      result.push(`\n![${alt}](${img.url})\n${credit}\n`);
    }
    result.push(sections[i]);
  }
  return result.join("\n");
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function toStyledHtml(title: string, meta: string, article: string): string {
  const htmlContent = marked.parse(article) as string;
  const safeTitle = escapeHtml(title);
  const safeMeta = escapeHtml(meta);
  return `<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>${safeTitle}</title>
<meta name="description" content="${safeMeta}">
<style>body{max-width:780px;margin:2rem auto;font-family:system-ui,sans-serif;line-height:1.7;color:#222;padding:0 1rem}
h1{font-size:2rem}h2{font-size:1.4rem;margin-top:2rem}img{max-width:100%;border-radius:8px}</style>
</head><body><h1>${safeTitle}</h1>${htmlContent}</body></html>`;
}

const LOAD_KEY = "mpchat-load-workspace";

export function WorkspaceClient() {
  const { t } = useI18n();
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [form, setForm] = useState<GenerateRequest>(EMPTY_FORM);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [seo, setSeo] = useState<AnalyzeResponse | null>(null);
  const [geo, setGeo] = useState<AnalyzeResponse | null>(null);
  const [changelog, setChangelog] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [optimizingMode, setOptimizingMode] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [copyMsg, setCopyMsg] = useState("");

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
  const [resultTab, setResultTab] = useState<ResultTab>("article");
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [wordCountTarget, setWordCountTarget] = useState(1200);
  const [pixabayKey, setPixabayKey] = useState("");
  const [pexelsKey, setPexelsKey] = useState("");
  const [batchMode, setBatchMode] = useState(false);
  const [batchScenarios, setBatchScenarios] = useState<string[]>([]);
  const [batchResults, setBatchResults] = useState<Array<{ scenario: string; result: GenerateResponse; seoScore: number; geoScore: number }>>([]);
  const [batchProgress, setBatchProgress] = useState(0);
  const [batchTotal, setBatchTotal] = useState(0);
  const [devtoKey, setDevtoKey] = useState("");
  const [hashnodeToken, setHashnodeToken] = useState("");
  const [hashnodePubId, setHashnodePubId] = useState("");
  const [mediumToken, setMediumToken] = useState("");
  const [paragraphKey, setParagraphKey] = useState("");
  const [publishDraft, setPublishDraft] = useState(true);
  const [publishResults, setPublishResults] = useState<Record<string, { status: string; data?: PublishResponse }>>({});
  const [aiDetect, setAiDetect] = useState<AiDetectResult | null>(null);
  const [translatedArticle, setTranslatedArticle] = useState<string | null>(null);
  const [translateTarget, setTranslateTarget] = useState("");
  const [isTranslating, setIsTranslating] = useState(false);
  const [translateOpen, setTranslateOpen] = useState(true);
  const [showWarmup, setShowWarmup] = useState(false);
  const [schemas, setSchemas] = useState<{ article_schema: Record<string, unknown>; faq_schema: Record<string, unknown> } | null>(null);
  const [internalLinks, setInternalLinks] = useState<Array<{ text: string; url: string }>>([]);

  const [configLoading, setConfigLoading] = useState(true);
  const [configOffline, setConfigOffline] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [ideationTargetTitle, setIdeationTargetTitle] = useState("");

  useEffect(() => {
    let retried = false;
    let cancelled = false;
    function applyConfig(data: ConfigData) {
      if (cancelled) return;
      setConfig(data);
      const category = Object.keys(data.scenario_categories)[0] || "";
      const firstScenario = data.scenario_categories[category]?.[0];
      const firstProvider = data.providers.find((p) => p.id === "gemini") || data.providers[0];
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
      setConfigLoading(false);
    }
    function loadConfig() {
      api.getConfig().then((data) => {
        applyConfig(data);
        setConfigOffline(false);
      }).catch(() => {
        if (!retried) {
          retried = true;
          setTimeout(loadConfig, 3000);
        } else {
          applyConfig(FALLBACK_CONFIG);
          setConfigOffline(true);
        }
      });
    }
    loadConfig();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(LOAD_KEY);
      if (raw) {
        window.localStorage.removeItem(LOAD_KEY);
        const item = JSON.parse(raw);
        if (item?.result) {
          setResult(item.result);
          setSeo({ score: item.seoScore, breakdown: {}, suggestions: [], details: {} });
          setGeo({ score: item.geoScore, breakdown: {}, suggestions: [], details: {} });
          setForm((prev) => ({ ...prev, keywords: item.keywords || prev.keywords, scenario: item.scenario || prev.scenario }));
        }
      }
    } catch { /* noop */ }

    // Prefill from ideation page
    try {
      const prefill = window.localStorage.getItem("mpchat-ideation-prefill");
      if (prefill) {
        window.localStorage.removeItem("mpchat-ideation-prefill");
        const item = JSON.parse(prefill);
        if (item?.keywords) {
          setForm((prev) => ({ ...prev, keywords: item.keywords }));
        }
        if (item?.title) {
          setIdeationTargetTitle(item.title);
        }
      }
    } catch { /* noop */ }
  }, []);

  useEffect(() => {
    if (form.provider && form.api_key) {
      saveAiConfig({ provider: form.provider, model: form.model, api_key: form.api_key, base_url: form.base_url });
    }
  }, [form.provider, form.model, form.api_key, form.base_url]);

  const selectedProvider = useMemo(() => config?.providers?.find((p) => p.id === form.provider), [config, form.provider]);
  const scenarios = useMemo(() => (config ? config.scenario_categories[form.category] || [] : []), [config, form.category]);
  const selectedScenario = useMemo(() => scenarios.find((s) => s.label === form.scenario), [scenarios, form.scenario]);
  const allScenarios = useMemo(() => {
    if (!config) return [];
    return Object.entries(config.scenario_categories).flatMap(([cat, list]) => list.map((s) => ({ ...s, category: cat })));
  }, [config]);

  const translateTargets = useMemo(
    () => getTranslateTargets(form.language),
    [form.language],
  );

  useEffect(() => {
    setTranslatedArticle(null);
  }, [form.language]);

  function updateForm<K extends keyof GenerateRequest>(key: K, value: GenerateRequest[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }
  function handleCategoryChange(category: string) {
    const next = config?.scenario_categories[category]?.[0];
    setForm((prev) => ({ ...prev, category, scenario: next?.label || "", keywords: next?.keywords || "", selling_points: next?.selling_points || [] }));
  }
  function handleScenarioChange(label: string) {
    const next = scenarios.find((s) => s.label === label);
    setForm((prev) => ({ ...prev, scenario: label, keywords: next?.keywords || prev.keywords, selling_points: next?.selling_points || prev.selling_points }));
  }
  function handleProviderChange(providerId: string) {
    const next = config?.providers?.find((p) => p.id === providerId);
    const newKey = providerId === "gemini" ? DEFAULT_GEMINI_KEY : providerId === "kimi" ? DEFAULT_KIMI_KEY : "";
    setForm((prev) => ({ ...prev, provider: providerId, model: next?.models?.[0] || prev.model, base_url: next?.base_url || prev.base_url, api_key: newKey }));
  }
  function toggleSellingPoint(point: string) {
    setForm((prev) => {
      const has = prev.selling_points.includes(point);
      return { ...prev, selling_points: has ? prev.selling_points.filter((p) => p !== point) : [...prev.selling_points, point] };
    });
  }

  async function runAnalyses(nextResult: GenerateResponse, keywords: string, sellingPoints?: string[]) {
    const [seoResp, geoResp] = await Promise.all([
      api.analyzeSeo(nextResult.article, keywords),
      api.analyzeGeo(nextResult.article, keywords, nextResult.faq_pairs),
    ]);
    setSeo(seoResp);
    setGeo(geoResp);
    try {
      const [schemaResp, linksResp] = await Promise.all([
        api.getSchema({ title: nextResult.title, description: nextResult.meta_description, faq_pairs: nextResult.faq_pairs }),
        api.getInternalLinks(sellingPoints ?? form.selling_points),
      ]);
      setSchemas(schemaResp);
      setInternalLinks(linksResp.links || []);
    } catch { /* noop */ }
    pushHistory({ id: crypto.randomUUID(), createdAt: new Date().toISOString(), scenario: form.scenario, keywords, result: nextResult, seoScore: seoResp.score, geoScore: geoResp.score });
  }

  function validate(): string | null {
    if (!form.api_key.trim()) return t("err.invalidKey");
    if (!form.keywords.trim()) return "请输入关键词";
    if (!form.category) return "请选择分类";
    if (!form.scenario) return "请选择场景";
    return null;
  }

  async function handleGenerate(overrideTargetTitle?: string) {
    const err = validate();
    if (err) { setError(err); return; }
    const titleToUse = overrideTargetTitle !== undefined ? overrideTargetTitle : ideationTargetTitle;
    const warmupTimer = setTimeout(() => setShowWarmup(true), 5000);
    try { setIsLoading(true); setError(""); setChangelog([]); setAiDetect(null); setSchemas(null); setSeo(null); setGeo(null); setTranslatedArticle(null);
      const generated = await api.generate({ ...form, word_count_target: wordCountTarget, target_title: titleToUse || undefined });
      setResult(generated);
      setIdeationTargetTitle("");
      await runAnalyses(generated, form.keywords, form.selling_points);
    } catch (e) { setError(e instanceof Error ? e.message : t("err.requestFailed")); } finally { clearTimeout(warmupTimer); setShowWarmup(false); setIsLoading(false); }
  }

  async function handleOptimize(mode: "seo" | "geo" | "dual" | "triple" | "humanize") {
    if (!result) return;
    const warmupTimer = setTimeout(() => setShowWarmup(true), 8000);
    try {
      setIsLoading(true); setOptimizingMode(mode); setError(""); setSeo(null); setGeo(null);
      const optimized = await api.optimize({ provider: form.provider, api_key: form.api_key, model: form.model, base_url: form.base_url, article: result.article, keywords: form.keywords, mode });
      const nextResult = { ...result, article: optimized.optimized_article };
      setResult(nextResult); setChangelog(optimized.changelog);
      await runAnalyses(nextResult, form.keywords, form.selling_points);
    } catch (e) {
      setError(e instanceof Error ? e.message : "优化失败，后端处理时间较长，请稍后重试");
    } finally { clearTimeout(warmupTimer); setShowWarmup(false); setIsLoading(false); setOptimizingMode(null); }
  }

  function parseAiDetectResult(raw: unknown): AiDetectResult {
    if (raw == null) return { score: 0, traces: [], high_risk_paragraphs: [], summary: "" };
    if (raw && typeof raw === "object" && "score" in raw) { const result = raw as AiDetectResult; if (result.score > 1) result.score = result.score / 100; return result; }
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
    if (!result) return;
    try { setIsLoading(true); setError("");
      const resp = await api.detectAi({ api_key: form.api_key, model: form.model, base_url: form.base_url, article: result.article, provider: form.provider });
      setAiDetect(parseAiDetectResult(resp.result));
    } catch (e) { setError(e instanceof Error ? e.message : "检测失败"); } finally { setIsLoading(false); }
  }

  async function handleTranslate(targetLang: string) {
    if (!result) return;
    try {
      setIsTranslating(true);
      setTranslatedArticle(null);
      setTranslateTarget(targetLang);
      const resp = await api.translate({
        provider: form.provider,
        api_key: form.api_key,
        base_url: form.base_url,
        model: form.model,
        article: result.article,
        source_lang: form.language || "中文 (Chinese)",
        target_lang: targetLang,
      });
      setTranslatedArticle(resp.translated_article);
      setTranslateOpen(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "翻译失败，请稍后重试");
    } finally {
      setIsTranslating(false);
    }
  }

  async function handlePublish(platform: string) {
    if (!result) return;
    try {
      setPublishResults((prev) => ({ ...prev, [platform]: { status: "loading" } }));
      const resp = await api.publishTo(platform, { title: result.title, article: result.article, meta_description: result.meta_description, slug: result.slug, tags: form.keywords.split(",").map((k) => k.trim()).filter(Boolean), published: !publishDraft, api_key: devtoKey, token: hashnodeToken, publication_id: hashnodePubId, medium_token: mediumToken, paragraph_key: paragraphKey });
      setPublishResults((prev) => ({ ...prev, [platform]: { status: "done", data: resp } }));
    } catch (e) {
      setPublishResults((prev) => ({ ...prev, [platform]: { status: "error", data: { preview: e instanceof Error ? e.message : "失败" } } }));
    }
  }

  const handleBatchGenerate = useCallback(async () => {
    if (batchScenarios.length === 0 || !form.api_key.trim()) return;
    try { setIsLoading(true); setError(""); setBatchResults([]); setBatchProgress(0); setBatchTotal(batchScenarios.length);
      const results: typeof batchResults = [];
      const failed: string[] = [];
      for (let i = 0; i < batchScenarios.length; i++) {
        const scenarioLabel = batchScenarios[i];
        const found = allScenarios.find((s) => s.label === scenarioLabel);
        if (!found) { failed.push(scenarioLabel); continue; }
        setBatchProgress(i + 1);
        try {
          const generated = await api.generate({ ...form, category: found.category, scenario: scenarioLabel, keywords: found.keywords || form.keywords, selling_points: found.selling_points || [] });
          const [seoR, geoR] = await Promise.all([ api.analyzeSeo(generated.article, found.keywords || form.keywords), api.analyzeGeo(generated.article, found.keywords || form.keywords, generated.faq_pairs) ]);
          results.push({ scenario: scenarioLabel, result: generated, seoScore: seoR.score, geoScore: geoR.score });
          pushHistory({ id: crypto.randomUUID(), createdAt: new Date().toISOString(), scenario: scenarioLabel, keywords: found.keywords || form.keywords, result: generated, seoScore: seoR.score, geoScore: geoR.score });
        } catch { failed.push(scenarioLabel); }
      }
      setBatchResults(results);
      if (failed.length > 0) {
        setError(`${results.length} 个场景成功，${failed.length} 个失败: ${failed.join(", ")}`);
      }
    } catch (e) { setError(e instanceof Error ? e.message : "批量生成失败"); } finally { setIsLoading(false); }
  }, [batchScenarios, form, allScenarios]);

  function handleAdoptTitle(title: string) { if (!result) return; setResult({ ...result, title }); }

  function downloadBatchAll() {
    const md = batchResults.map((b) => `# ${b.result.title}\n\n> ${b.result.meta_description}\n\n**场景:** ${b.scenario} | **SEO:** ${b.seoScore} | **GEO:** ${b.geoScore}\n\n---\n\n${b.result.article}`).join("\n\n---\n\n");
    downloadFile(md, "batch-articles.md", "text/markdown");
  }

  const keywordDensity = useMemo(() => {
    const bd = seo?.breakdown as Record<string, unknown> | undefined;
    const kd = bd?.keyword_density;
    if (!kd || typeof kd !== "object") return [];
    return Object.entries(kd as Record<string, unknown>).map(([k, v]) => ({
      keyword: k,
      density: typeof v === "number" ? v : (v && typeof v === "object" && "density_pct" in v) ? (v as Record<string, number>).density_pct : 0,
    }));
  }, [seo]);

  return (
    <div className="page-shell">
      <section className="hero-card">
        <div>
          <span className="eyebrow">MPChat v5</span>
          <h1>内容工作台</h1>
          <p>生成、分析、优化与分发 —— 全流程一站式完成。</p>
        </div>
        <div className="hero-stats">
          <div className="metric-card"><span>场景数</span><strong>{config ? Object.values(config.scenario_categories).flat().length : "--"}</strong></div>
          <div className="metric-card"><span>字数目标</span><strong>{wordCountTarget}</strong></div>
          <div className="metric-card"><span>状态</span><strong>{isLoading ? "处理中" : "可用"}</strong></div>
        </div>
      </section>

      <section className="glass-card" style={{position:"relative"}}>
        {configLoading && <div style={{position:"absolute",inset:0,display:"flex",alignItems:"center",justifyContent:"center",background:"rgba(0,0,0,0.4)",borderRadius:"inherit",zIndex:10,fontSize:"1.1rem",color:"var(--muted)"}}>配置加载中...</div>}
        <div className="section-header">
          <div><h2>创作配置</h2><p>服务商、场景、文风、SERP/GEO 等一次配置完成。</p></div>
          <div className="action-row">
            {batchMode ? (
              <button className="primary-button" onClick={handleBatchGenerate} disabled={isLoading || batchScenarios.length === 0}>
                {isLoading ? `批量中 ${batchProgress}/${batchTotal}` : `批量生成 (${batchScenarios.length})`}
              </button>
            ) : (
              <button
                className="primary-button"
                onClick={() => handleGenerate()}
                disabled={isLoading || !config}
                style={ideationTargetTitle ? { opacity: 0.5 } : undefined}
                title={ideationTargetTitle ? `使用下方选题 Banner 的「立即生成」按钮，以确保基于目标标题生成` : undefined}
              >
                {isLoading ? t("msg.generating") : ideationTargetTitle ? "按场景生成（忽略选题）" : t("btn.generate")}
              </button>
            )}
          </div>
        </div>
        <div className="form-grid">
          <label><span>Provider</span><select value={form.provider} onChange={(e) => handleProviderChange(e.target.value)}>{(config?.providers ?? []).map((p) => (<option key={p.id} value={p.id}>{p.label}</option>))}</select></label>
          <label><span>Model</span><select value={form.model} onChange={(e) => updateForm("model", e.target.value)}>{(selectedProvider?.models || [form.model]).map((m) => (<option key={m} value={m}>{m}</option>))}</select></label>
          <label><span>Language</span><select value={form.language} onChange={(e) => updateForm("language", e.target.value)}>{Object.keys(config?.languages || {}).map((l) => (<option key={l} value={l}>{l}</option>))}</select></label>
          <label><span>Style</span><select value={form.style} onChange={(e) => updateForm("style", e.target.value)}>{Object.keys(config?.article_styles || {}).map((s) => (<option key={s} value={s}>{s}</option>))}</select></label>
          <label><span>Category</span><select value={form.category} onChange={(e) => handleCategoryChange(e.target.value)}>{Object.keys(config?.scenario_categories || {}).map((c) => (<option key={c} value={c}>{c}</option>))}</select></label>
          <label><span>Scenario</span><select value={form.scenario} onChange={(e) => handleScenarioChange(e.target.value)}>{scenarios.map((s) => (<option key={s.label} value={s.label}>{s.label}</option>))}</select></label>
          <label><span>API Key {selectedProvider?.get_key_url ? <a href={selectedProvider.get_key_url} target="_blank" rel="noreferrer" style={{color:"var(--primary)",fontSize:"0.75rem",marginLeft:4}}>获取</a> : null}</span><div style={{position:"relative"}}><input type={showApiKey ? "text" : "password"} value={form.api_key} onChange={(e) => updateForm("api_key", e.target.value)} placeholder="必填" style={{paddingRight:40}} /><button type="button" onClick={() => setShowApiKey((v) => !v)} style={{position:"absolute",right:8,top:"50%",transform:"translateY(-50%)",background:"none",border:"none",cursor:"pointer",color:"var(--muted)",fontSize:"0.85rem",padding:0}} title={showApiKey ? "隐藏" : "查看"}>{showApiKey ? "🙈" : "👁"}</button></div></label>
          <label><span>Base URL</span><input value={form.base_url} onChange={(e) => updateForm("base_url", e.target.value)} /></label>
          <label className="span-4">
            <span style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>Keywords</span>
              <Link href="/ideation" style={{ fontSize: "0.75rem", color: "var(--primary)", textDecoration: "none" }}>✦ {t("ideation.shortcut")}</Link>
            </span>
            <textarea value={form.keywords} onChange={(e) => updateForm("keywords", e.target.value)} rows={2} />
          </label>
        </div>

        {config?.keyword_presets && config.keyword_presets.length > 0 && (
          <div style={{marginTop:12}}><span className="subtle-label">关键词预设</span>
            <div className="pill-row" style={{marginTop:6}}>{config.keyword_presets.map((p) => (<button key={p.label} className="pill preset-chip" onClick={() => updateForm("keywords", p.keywords)} title={`难度: ${p.difficulty}`}>{p.label}</button>))}</div>
          </div>
        )}

        {config?.selling_point_groups && Object.keys(config.selling_point_groups).length > 0 && (
          <div style={{marginTop:16}}><span className="subtle-label">卖点选择</span>
            <div className="sp-groups">{Object.entries(config.selling_point_groups).map(([group, points]) => (
              <div key={group} className="sp-group"><strong className="sp-group-title">{group}</strong>
                <div className="sp-checks">{Object.entries(points).map(([, text]) => (<label key={text} className="sp-check"><input type="checkbox" checked={form.selling_points.includes(text)} onChange={() => toggleSellingPoint(text)} /><span>{text}</span></label>))}</div>
              </div>
            ))}</div>
          </div>
        )}

        {selectedScenario && form.selling_points.length === 0 && (
          <div className="pill-row" style={{marginTop:8}}><span className="subtle-label">场景默认卖点</span>
            {((selectedScenario as Scenario).selling_points ?? []).map((sp) => (<button className="pill preset-chip" key={sp} onClick={() => toggleSellingPoint(sp)}>{sp}</button>))}
          </div>
        )}

        <div className="form-grid" style={{marginTop:14}}>
          <label className="span-2"><span>字数目标: {wordCountTarget}</span><input type="range" min={600} max={3000} step={100} value={wordCountTarget} onChange={(e) => setWordCountTarget(Number(e.target.value))} /></label>
          <label className="span-2"><span>配图数量: {form.image_count}</span><input type="range" min={0} max={5} step={1} value={form.image_count} onChange={(e) => updateForm("image_count", Number(e.target.value))} /></label>
        </div>

        <div className="toggle-row" style={{marginTop:14}}>
          <label className="toggle"><input type="checkbox" checked={form.include_images} onChange={(e) => updateForm("include_images", e.target.checked)} /><span>配图</span></label>
          <label className="toggle"><input type="checkbox" checked={form.use_web} onChange={(e) => updateForm("use_web", e.target.checked)} /><span>网页知识库</span></label>
          <label className="toggle"><input type="checkbox" checked={form.use_serp} onChange={(e) => updateForm("use_serp", e.target.checked)} /><span>SERP 分析</span></label>
          <label className="toggle"><input type="checkbox" checked={form.geo_mode} onChange={(e) => updateForm("geo_mode", e.target.checked)} /><span>GEO 模式</span></label>
          <label className="toggle"><input type="checkbox" checked={batchMode} onChange={(e) => setBatchMode(e.target.checked)} /><span>批量模式</span></label>
        </div>

        <details open={advancedOpen} onToggle={(e) => setAdvancedOpen((e.target as HTMLDetailsElement).open)} style={{marginTop:16}}>
          <summary className="collapse-header">高级配置</summary>
          <div className="form-grid" style={{marginTop:10}}>
            <label className="span-2"><span>Pixabay API Key</span><input value={pixabayKey} onChange={(e) => setPixabayKey(e.target.value)} placeholder="可选" /></label>
            <label className="span-2"><span>Pexels API Key</span><input value={pexelsKey} onChange={(e) => setPexelsKey(e.target.value)} placeholder="可选" /></label>
          </div>
        </details>
      </section>

      {batchMode && (
        <section className="glass-card"><h3>选择批量场景</h3>
          <div className="sp-checks" style={{marginTop:8}}>{allScenarios.map((s) => (
            <label key={s.label} className="sp-check"><input type="checkbox" checked={batchScenarios.includes(s.label)} onChange={() => setBatchScenarios((prev) => prev.includes(s.label) ? prev.filter((x) => x !== s.label) : [...prev, s.label])} /><span>{s.category} / {s.label}</span></label>
          ))}</div>
        </section>
      )}

      {configOffline && <div className="error-banner" style={{background:"rgba(255,165,0,0.15)",borderColor:"rgba(255,165,0,0.4)",color:"#ffaa33"}}>使用离线配置，部分场景数据可能不完整。后端连接恢复后请刷新页面。</div>}
      {ideationTargetTitle && (
        <div className="error-banner" style={{background:"rgba(99,91,255,0.12)",borderColor:"rgba(99,91,255,0.35)",color:"var(--primary)"}}>
          <div style={{display:"flex",alignItems:"center",gap:12,flexWrap:"wrap"}}>
            <span style={{flex:1}}>✦ {t("ideation.targetTitleHint")}: <strong>{ideationTargetTitle}</strong></span>
            <button className="primary-button" style={{padding:"6px 16px",fontSize:"0.85rem"}} disabled={isLoading || !config} onClick={() => { handleGenerate(ideationTargetTitle); }}>
              {isLoading ? t("msg.generating") : t("ideation.generateNow")}
            </button>
            <button onClick={() => setIdeationTargetTitle("")} style={{background:"none",border:"none",cursor:"pointer",color:"var(--muted)",fontSize:"1rem",padding:0}} title="关闭">✕</button>
          </div>
        </div>
      )}      {error ? <div className="error-banner toast-error" onClick={() => setError("")}><span>{error}</span><span style={{cursor:"pointer",marginLeft:12,opacity:0.6}}>✕</span></div> : null}
      {copyMsg && <div className="error-banner toast-error" style={{background:"rgba(34,197,94,0.15)",borderColor:"rgba(34,197,94,0.3)",color:"#4ade80"}}>{copyMsg}</div>}

      {showWarmup && (
        <div className="warmup-banner">
          <div className="warmup-spinner" />
          <span>{optimizingMode ? `AI 正在${optimizingMode === "triple" ? "三合一" : optimizingMode === "dual" ? "双重" : optimizingMode.toUpperCase()}优化，可能需要 30-60 秒...` : "AI 正在生成文章，可能需要 30-60 秒..."}</span>
        </div>
      )}

      {batchMode && batchResults.length > 0 && (
        <section className="glass-card">
          <div className="section-header"><h2>批量结果 ({batchResults.length})</h2><button className="secondary-button" onClick={downloadBatchAll}>全部下载 (Markdown)</button></div>
          <div className="stack-column">{batchResults.map((b, i) => (
            <div key={b.scenario} className="glass-card" style={{background:"rgba(255,255,255,0.02)"}}>
              <div className="section-header"><div><h3>{b.result.title}</h3><p className="muted-text">{b.scenario}</p></div>
                <div className="score-strip"><div className="score-card"><span>SEO</span><strong>{b.seoScore}</strong></div><div className="score-card"><span>GEO</span><strong>{b.geoScore}</strong></div></div>
              </div>
              <div className="article-card clamp-article rendered-article"><ReactMarkdown remarkPlugins={[remarkGfm]}>{b.result.article}</ReactMarkdown></div>
              <button className="secondary-button" style={{marginTop:8}} onClick={() => downloadFile(b.result.article, `${b.result.slug || b.scenario}.md`, "text/markdown")}>下载</button>
            </div>
          ))}</div>
        </section>
      )}

      {result && !batchMode ? (
        <>
          <section className="score-strip" style={{alignItems:"center"}}>
            <ScoreRing score={seo?.score ?? 0} label="SEO" />
            <ScoreRing score={geo?.score ?? 0} label="GEO" />
            <div className="action-row" style={{marginLeft:"auto"}}>
              <button className="secondary-button" onClick={() => handleOptimize("seo")} disabled={isLoading}>{optimizingMode === "seo" ? "SEO 优化中..." : "SEO 优化"}</button>
              <button className="secondary-button" onClick={() => handleOptimize("geo")} disabled={isLoading}>{optimizingMode === "geo" ? "GEO 优化中..." : "GEO 优化"}</button>
              <button className="secondary-button" onClick={() => handleOptimize("dual")} disabled={isLoading}>{optimizingMode === "dual" ? "双优化中..." : "双优化"}</button>
              <button className="primary-button" onClick={() => handleOptimize("triple")} disabled={isLoading}>{optimizingMode === "triple" ? "三合一优化中..." : "三合一优化"}</button>
              {((seo?.score ?? 100) < 90 || (geo?.score ?? 100) < 90) && (
                <button className="primary-button" onClick={() => handleOptimize("triple")} disabled={isLoading} style={{background:"linear-gradient(135deg,var(--warning),var(--danger))"}}>{optimizingMode === "triple" ? "优化中..." : "一键优化到90+"}</button>
              )}
            </div>
          </section>

          <div className="tab-bar">
            {([["article","文章内容"],["seo-geo","SEO/GEO 分析"],["export","导出与复制"],["publish","分发"],["ai-detect","AI 检测"]] as [ResultTab,string][]).map(([id,label]) => (
              <button key={id} className={`tab-button ${resultTab === id ? "tab-active" : ""}`} onClick={() => setResultTab(id)}>{label}</button>
            ))}
          </div>

          {resultTab === "article" && (
            <section className="results-grid">
              <article className="glass-card">
                <div className="section-header"><div><h2>{result.title}</h2><p>{result.meta_description}</p></div><span className="slug-chip">/{result.slug}</span></div>
                <div className="pill-row">{(result.ab_titles ?? []).map((t) => (<button className="pill preset-chip" key={t} onClick={() => handleAdoptTitle(t)} title="点击采用此标题">{t}</button>))}</div>
                <div className="article-card rendered-article"><ReactMarkdown remarkPlugins={[remarkGfm]}>{interleaveImages(result.article, result.images ?? [])}</ReactMarkdown></div>
                <div className="glass-card" style={{marginTop:16,background:"rgba(255,255,255,0.03)"}}>
                  <div className="section-header" style={{marginBottom:translatedArticle ? 12 : 0}}>
                    <h3 style={{fontSize:"1rem",margin:0}}>{t("label.translate")}</h3>
                    <div className="action-row">
                      {translateTargets.map(({ lang, labelKey }) => (
                        <button
                          key={lang}
                          className="secondary-button"
                          onClick={() => handleTranslate(lang)}
                          disabled={isTranslating || isLoading}
                        >
                          {isTranslating && translateTarget === lang ? t("btn.translating") : t(labelKey)}
                        </button>
                      ))}
                    </div>
                  </div>
                  {translatedArticle && (
                    <details open={translateOpen} onToggle={(e) => setTranslateOpen((e.target as HTMLDetailsElement).open)}>
                      <summary className="collapse-header">{t("label.translateResult")} — {translateTarget}</summary>
                      <div style={{marginTop:12}}>
                        <div className="action-row" style={{marginBottom:8}}>
                          <button className="secondary-button" onClick={() => copyText(translatedArticle, setCopyMsg)}>{t("btn.copyTranslation")}</button>
                          <button className="secondary-button" onClick={() => downloadFile(translatedArticle, `${result.slug}-${translateTarget}.md`, "text/markdown")}>{t("btn.downloadTranslation")}</button>
                        </div>
                        <div className="article-card rendered-article"><ReactMarkdown remarkPlugins={[remarkGfm]}>{translatedArticle}</ReactMarkdown></div>
                      </div>
                    </details>
                  )}
                </div>
              </article>
              <aside className="stack-column">
                <div className="glass-card">
                  <h3>文章画像</h3>
                  <div className="mini-metrics"><div><span>字数</span><strong>{result.word_count}</strong></div><div><span>阅读时间</span><strong>{result.reading_time_min} min</strong></div></div>
                  {changelog.length > 0 && (<><h4>本次优化改动</h4><ul className="plain-list">{changelog.map((c) => (<li key={c}>{c}</li>))}</ul></>)}
                  <h4>优化建议</h4><ul className="plain-list">{(seo?.suggestions || []).concat(geo?.suggestions || []).slice(0,6).map((s) => (<li key={s}>{s}</li>))}</ul>
                </div>
                <div className="glass-card">
                  <h3>图片与提示词</h3>
                  <div className="image-grid">{(result.images ?? []).map((img) => (
                    <div key={img.url} style={{position:"relative"}}><Image src={img.url} alt={img.alt_text || result.title} className="preview-image" width={640} height={480} unoptimized />
                      {img.photographer && (<span style={{fontSize:"0.7rem",color:"var(--muted)",display:"block",marginTop:2}}>{img.photographer} ({img.source || ""})</span>)}
                    </div>
                  ))}</div>
                  {(result.image_prompts ?? []).length > 0 && (<><h4>AI 图片提示词</h4><ul className="plain-list">{(result.image_prompts ?? []).map((ip) => (<li key={ip.prompt}><strong>{ip.scene}</strong><p style={{margin:"4px 0 0",color:"var(--muted)",fontSize:"0.85rem"}}>{ip.prompt}</p></li>))}</ul></>)}
                </div>
                <div className="glass-card"><h3>FAQ</h3><ul className="plain-list">{(result.faq_pairs ?? []).map((f) => (<li key={f.q}><strong>{f.q}</strong><p>{f.a}</p></li>))}</ul></div>
              </aside>
            </section>
          )}

          {resultTab === "seo-geo" && (
            <section className="glass-card">
              <div className="seo-geo-grid">
                <div><h3>SEO 详情</h3>
                  <BreakdownBar label="H1 标题" value={Number(seo?.breakdown?.h1_count ?? 0)} max={2} />
                  <BreakdownBar label="H2 段落" value={Number(seo?.breakdown?.h2_count ?? 0)} max={6} />
                  <BreakdownBar label="字数" value={Number(seo?.breakdown?.word_count ?? 0)} max={2000} />
                  <BreakdownBar label="CTA" value={seo?.breakdown?.has_cta ? 100 : 0} max={100} />
                  <div style={{marginTop:12}}><strong style={{fontSize:"0.85rem"}}>CTA 检测</strong><p className="muted-text" style={{fontSize:"0.85rem"}}>{seo?.breakdown?.has_cta ? "已包含 CTA" : "未检测到 CTA，建议在文末添加引导"}</p></div>
                </div>
                <div><h3>GEO 详情</h3>{geo?.breakdown && Object.entries(geo.breakdown).map(([k,v]) => (<BreakdownBar key={k} label={k} value={Number(v) || 0} max={100} />))}</div>
              </div>
              {keywordDensity.length > 0 && (<div style={{marginTop:20}}><h3>关键词密度</h3><table className="kw-table"><thead><tr><th>关键词</th><th>密度</th></tr></thead><tbody>{keywordDensity.map((kd) => (<tr key={kd.keyword}><td>{kd.keyword}</td><td>{typeof kd.density === "number" ? kd.density.toFixed(2) : "0.00"}%</td></tr>))}</tbody></table></div>)}
              {result.serp && (<div style={{marginTop:20}}><h3>SERP 分析结果</h3><pre className="article-card" style={{maxHeight:300,overflow:"auto"}}>{JSON.stringify(result.serp, null, 2)}</pre></div>)}
              {schemas && (<div style={{marginTop:20}}><h3>JSON-LD Schema</h3><div className="seo-geo-grid">
                <div><h4>Article Schema</h4><pre className="article-card" style={{fontSize:"0.8rem",maxHeight:260,overflow:"auto"}}>{JSON.stringify(schemas.article_schema, null, 2)}</pre><button className="secondary-button" style={{marginTop:6}} onClick={() => copyText(JSON.stringify(schemas.article_schema, null, 2), setCopyMsg)}>复制</button></div>
                <div><h4>FAQPage Schema</h4><pre className="article-card" style={{fontSize:"0.8rem",maxHeight:260,overflow:"auto"}}>{JSON.stringify(schemas.faq_schema, null, 2)}</pre><button className="secondary-button" style={{marginTop:6}} onClick={() => copyText(JSON.stringify(schemas.faq_schema, null, 2), setCopyMsg)}>复制</button></div>
              </div></div>)}
              {internalLinks.length > 0 && (<div style={{marginTop:20}}><h3>推荐内部链接</h3><ul className="plain-list">{internalLinks.map((l) => (<li key={l.url}><a href={l.url} target="_blank" rel="noreferrer" style={{color:"var(--primary)"}}>{l.text}</a></li>))}</ul></div>)}
              <div style={{marginTop:20}}><h3>优化建议</h3><ul className="plain-list">{(seo?.suggestions || []).concat(geo?.suggestions || []).map((s) => (<li key={s}>{s}</li>))}</ul></div>
            </section>
          )}

          {resultTab === "export" && (
            <section className="glass-card">
              <h2>导出与复制</h2>
              <div className="export-grid">
                <div className="export-card"><h4>下载文件</h4><div className="action-row">
                  <button className="secondary-button" onClick={() => downloadFile(result.article, `${result.slug}.md`, "text/markdown")}>Markdown (.md)</button>
                  <button className="secondary-button" onClick={() => downloadFile(toStyledHtml(result.title, result.meta_description, result.article), `${result.slug}.html`, "text/html")}>HTML (.html)</button>
                  <button className="secondary-button" onClick={() => downloadFile(result.article.replace(/<[^>]*>/g, ""), `${result.slug}.txt`, "text/plain")}>纯文本 (.txt)</button>
                </div></div>
                <div className="export-card"><h4>复制内容</h4><div className="action-row">
                  <button className="secondary-button" onClick={() => copyText(result.article, setCopyMsg)}>复制 Markdown 源码</button>
                  <button className="secondary-button" onClick={() => copyText(`Title: ${result.title}\nDescription: ${result.meta_description}\nSlug: ${result.slug}\nKeywords: ${form.keywords}`, setCopyMsg)}>复制 SEO 元数据</button>
                  <button className="secondary-button" onClick={() => copyText((result.image_prompts ?? []).map((p) => `[${p.scene}] ${p.prompt}`).join("\n"), setCopyMsg)}>复制图片提示词</button>
                </div></div>
                <div className="export-card"><h4>AI 图片提示词</h4>{(result.image_prompts ?? []).length > 0 ? (<ul className="plain-list">{(result.image_prompts ?? []).map((ip) => (<li key={ip.prompt}><strong>{ip.scene}</strong>: {ip.prompt}</li>))}</ul>) : (<p className="muted-text">无图片提示词</p>)}</div>
              </div>
            </section>
          )}

          {resultTab === "publish" && (
            <section className="glass-card">
              <h2>内容分发</h2>
              <div className="form-grid" style={{marginBottom:16}}>
                <label><span>Dev.to API Key</span><input type="password" value={devtoKey} onChange={(e) => setDevtoKey(e.target.value)} /></label>
                <label><span>Hashnode Token</span><input type="password" value={hashnodeToken} onChange={(e) => setHashnodeToken(e.target.value)} /></label>
                <label><span>Hashnode Publication ID</span><input value={hashnodePubId} onChange={(e) => setHashnodePubId(e.target.value)} /></label>
                <label><span>Medium Integration Token</span><input type="password" placeholder="无 Token 则生成预览" value={mediumToken} onChange={(e) => setMediumToken(e.target.value)} /></label>
                <label><span>Paragraph API Key</span><input type="password" value={paragraphKey} onChange={(e) => setParagraphKey(e.target.value)} /></label>
                <label className="toggle" style={{alignSelf:"end"}}><input type="checkbox" checked={publishDraft} onChange={(e) => setPublishDraft(e.target.checked)} /><span>草稿模式</span></label>
              </div>
              <div className="publish-grid">{PLATFORMS.map((p) => {
                const pr = publishResults[p.id];
                return (<div key={p.id} className="publish-card">
                  <div className="section-header" style={{marginBottom:8}}><strong>{p.label}</strong>
                    <button className="secondary-button" onClick={() => handlePublish(p.id)} disabled={isLoading || pr?.status === "loading"} style={{padding:"6px 12px",fontSize:"0.82rem"}}>{pr?.status === "loading" ? "..." : p.needsKey ? "发布" : "生成预览"}</button>
                  </div>
                  {pr?.status === "done" && pr.data?.preview && (<div><pre className="article-card" style={{maxHeight:160,overflow:"auto",fontSize:"0.78rem"}}>{pr.data.preview}</pre><button className="secondary-button" style={{marginTop:6,padding:"4px 10px",fontSize:"0.78rem"}} onClick={() => copyText(pr.data?.preview || "", setCopyMsg)}>复制</button></div>)}
                  {pr?.status === "done" && pr.data?.url && (<a href={pr.data.url as string} target="_blank" rel="noreferrer" style={{color:"var(--primary)",fontSize:"0.82rem"}}>查看文章</a>)}
                  {pr?.status === "error" && (<p style={{color:"var(--danger)",fontSize:"0.82rem"}}>{pr.data?.preview || "发布失败"}</p>)}
                </div>);
              })}</div>
            </section>
          )}

          {resultTab === "ai-detect" && (
            <section className="glass-card">
              <h2>AI 检测与人性化</h2>
              <div className="action-row" style={{marginBottom:16}}>
                <button className="primary-button" onClick={handleDetectAi} disabled={isLoading}>{isLoading ? "检测中..." : "检测 AI 痕迹"}</button>
                <button className="secondary-button" onClick={() => handleOptimize("humanize")} disabled={isLoading}>人性化改写</button>
                <button className="primary-button" onClick={() => handleOptimize("triple")} disabled={isLoading} style={{background:"linear-gradient(135deg,#ff6b81,#7c8cff)"}}>三重优化 (SEO+GEO+人性化)</button>
              </div>
              {aiDetect && (<div>
                <div className="score-strip" style={{marginBottom:16}}>
                  <ScoreRing score={Math.round((1 - aiDetect.score) * 100)} label="人性化得分" size={100} />
                  <div className="glass-card" style={{flex:1,padding:16}}><h4>检测摘要</h4><div className="rendered-article" style={{fontSize:"0.9rem"}}><ReactMarkdown remarkPlugins={[remarkGfm]}>{aiDetect.summary}</ReactMarkdown></div></div>
                </div>
                {(aiDetect.traces?.length ?? 0) > 0 && (<div style={{marginBottom:16}}><h4>AI 痕迹</h4><ul className="plain-list">{(aiDetect.traces ?? []).map((tr) => (<li key={tr} style={{color:"var(--warning)"}}>{tr}</li>))}</ul></div>)}
                {(aiDetect.high_risk_paragraphs?.length ?? 0) > 0 && (<div><h4>高风险段落</h4>{(aiDetect.high_risk_paragraphs ?? []).map((p, i) => (<pre key={i} className="article-card" style={{borderColor:"rgba(255,107,129,0.3)",marginBottom:8,fontSize:"0.85rem"}}>{p}</pre>))}</div>)}
              </div>)}
            </section>
          )}
        </>
      ) : null}
    </div>
  );
}
