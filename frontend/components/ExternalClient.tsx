"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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

type SeoData = {
  word_count?: number;
  cn_chars?: number;
  en_words?: number;
  reading_time_min?: number;
  h1_count?: number;
  h2_count?: number;
  has_cta?: boolean;
  keyword_density?: Record<string, { count: number; density_pct: number }>;
  structure_score?: number;
};

type GeoData = {
  score?: number;
  issues?: string[];
  tips?: string[];
  details?: {
    answer_first_len?: number;
    question_h2_ratio?: number;
    citation_count?: number;
    long_paragraphs?: number;
    entity_mentions?: number;
    faq_count?: number;
    authority_refs?: number;
  };
};

type LoadingAction = null | "analyze" | "seo" | "geo" | "dual" | "triple" | "humanize" | "detect" | "translate";
type ProgressStage = "" | "analyzing" | "optimizing" | "rescoring";

function downloadFile(content: string, filename: string, mime = "text/plain") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function CheckItem({ pass, label, detail }: { pass: boolean; label: string; detail?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 8, padding: "6px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
      <span style={{ fontSize: "1.1rem", flexShrink: 0, marginTop: 1 }}>{pass ? "✅" : "❌"}</span>
      <div style={{ flex: 1 }}>
        <span style={{ color: pass ? "var(--success)" : "var(--danger)", fontWeight: 500 }}>{label}</span>
        {detail && <p style={{ margin: "2px 0 0", fontSize: "0.82rem", color: "var(--muted)", lineHeight: 1.4 }}>{detail}</p>}
      </div>
    </div>
  );
}

function countWords(text: string): { cn: number; en: number; total: number } {
  const cn = (text.match(/[\u4e00-\u9fff]/g) || []).length;
  const en = (text.match(/[a-zA-Z]+/g) || []).length;
  return { cn, en, total: cn + en };
}

function countKeywordOccurrences(text: string, keywords: string): Record<string, number> {
  if (!keywords.trim()) return {};
  const result: Record<string, number> = {};
  const lower = text.toLowerCase();
  keywords.split(",").map(k => k.trim()).filter(Boolean).slice(0, 10).forEach(kw => {
    const re = new RegExp(kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi");
    result[kw] = (lower.match(re) || []).length;
  });
  return result;
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
  const [analysis, setAnalysis] = useState<{ seo: SeoData; geo: GeoData } | null>(null);
  const [optimized, setOptimized] = useState<OptimizeResponse | null>(null);
  const [error, setError] = useState("");
  const [copyMsg, setCopyMsg] = useState("");
  const [loadingAction, setLoadingAction] = useState<LoadingAction>(null);
  const [progressStage, setProgressStage] = useState<ProgressStage>("");
  const [originalArticle, setOriginalArticle] = useState("");
  const [showDiff, setShowDiff] = useState(false);
  const [aiDetect, setAiDetect] = useState<AiDetectResult | null>(null);
  const [translatedArticle, setTranslatedArticle] = useState<string | null>(null);
  const [translateTarget, setTranslateTarget] = useState("");
  const [translateOpen, setTranslateOpen] = useState(true);

  const loading = loadingAction !== null;

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

  useEffect(() => {
    if (aiCfg.provider && aiCfg.api_key) saveAiConfig(aiCfg);
  }, [aiCfg.provider, aiCfg.model, aiCfg.api_key, aiCfg.base_url]);

  const configLabel = useMemo(() => {
    const providerNames: Record<string, string> = {
      gemini: "Google Gemini", openai: "OpenAI", anthropic: "Anthropic", deepseek: "DeepSeek",
      kimi: "Kimi", groq: "Groq", together: "Together AI", siliconflow: "SiliconFlow",
      zhipu: "Zhipu AI", openrouter: "OpenRouter", custom: "Custom",
    };
    return providerNames[aiCfg.provider] || aiCfg.provider;
  }, [aiCfg.provider]);

  const wordStats = useMemo(() => countWords(article), [article]);
  const kwOccurrences = useMemo(() => countKeywordOccurrences(article, keywords), [article, keywords]);

  const actionLabels: Record<string, string> = {
    analyze: "分析中...",
    seo: "SEO 优化中...",
    geo: "GEO 优化中...",
    dual: "双优化中...",
    triple: "三合一优化中...",
    humanize: "人性化改写中...",
    detect: "AI 检测中...",
    translate: t("btn.translating"),
  };

  const stageLabels: Record<string, string> = {
    analyzing: "正在分析文章结构...",
    optimizing: "AI 正在优化文章...",
    rescoring: "正在重新评分...",
  };

  async function handleAnalyze() {
    const warmupTimer = setTimeout(() => setShowWarmup(true), 5000);
    try {
      setLoadingAction("analyze");
      setProgressStage("analyzing");
      setError("");
      const data = await api.analyzeExternal(article, keywords);
      setAnalysis(data as unknown as { seo: SeoData; geo: GeoData });
    } catch (err) {
      setError(err instanceof Error ? err.message : "分析失败");
    } finally {
      clearTimeout(warmupTimer); setShowWarmup(false); setLoadingAction(null); setProgressStage("");
    }
  }

  async function handleOptimize(mode: "seo" | "geo" | "dual" | "triple" | "humanize") {
    const warmupTimer = setTimeout(() => setShowWarmup(true), 8000);
    try {
      setLoadingAction(mode);
      setProgressStage("optimizing");
      setError("");
      setAnalysis(null);
      setAiDetect(null);
      setTranslatedArticle(null);
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
      setProgressStage("rescoring");
      try {
        const refreshed = await api.analyzeExternal(data.optimized_article, keywords);
        setAnalysis(refreshed as unknown as { seo: SeoData; geo: GeoData });
      } catch {
        setError("优化成功，但分析刷新失败，请手动点击分析");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "优化失败");
    } finally {
      clearTimeout(warmupTimer); setShowWarmup(false); setLoadingAction(null); setProgressStage("");
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
    if (raw && typeof raw === "object" && "score" in raw) {
      const result = raw as AiDetectResult;
      if (result.score > 1) result.score = result.score / 100;
      return result;
    }
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
    const warmupTimer = setTimeout(() => setShowWarmup(true), 8000);
    try {
      setLoadingAction("detect");
      setProgressStage("analyzing");
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
      clearTimeout(warmupTimer); setShowWarmup(false); setLoadingAction(null); setProgressStage("");
    }
  }

  async function handleTranslateExternal(targetLang: string) {
    if (!article.trim()) return;
    try {
      setLoadingAction("translate");
      setProgressStage("optimizing");
      setError("");
      setTranslatedArticle(null);
      setTranslateTarget(targetLang);
      const resp = await api.translateExternal({
        provider: aiCfg.provider,
        api_key: aiCfg.api_key,
        base_url: aiCfg.base_url,
        model: aiCfg.model,
        article,
        source_lang: "中文 (Chinese)",
        target_lang: targetLang,
      });
      setTranslatedArticle(resp.translated_article);
      setTranslateOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "翻译失败，请稍后重试");
    } finally {
      setLoadingAction(null);
      setProgressStage("");
    }
  }

  const doCopy = useCallback((text: string) => {
    navigator.clipboard.writeText(text).then(() => setCopyMsg("已复制")).catch(() => setCopyMsg("复制失败"));
  }, []);

  function btnLabel(action: string, defaultLabel: string): string {
    if (loadingAction === action) return actionLabels[action] || "处理中...";
    return defaultLabel;
  }

  function renderSeoChecklist(seo: SeoData) {
    const wc = seo.word_count ?? 0;
    const h1 = seo.h1_count ?? 0;
    const h2 = seo.h2_count ?? 0;
    const cta = seo.has_cta ?? false;
    const kd = seo.keyword_density ?? {};
    const kdEntries = Object.entries(kd);
    const avgDensity = kdEntries.length > 0 ? kdEntries.reduce((s, [, v]) => s + v.density_pct, 0) / kdEntries.length : 0;

    return (
      <div>
        <CheckItem pass={h1 === 1} label={`H1 标题: ${h1} 个`} detail={h1 === 1 ? "正确，仅一个 H1 标题" : h1 === 0 ? "缺少 H1 标题，建议添加一个主标题" : `有 ${h1} 个 H1，建议只保留 1 个`} />
        <CheckItem pass={h2 >= 3} label={`H2 副标题: ${h2} 个`} detail={h2 >= 3 ? "结构合理" : `建议至少 3 个 H2 副标题以改善文章结构`} />
        <CheckItem pass={wc >= 600 && wc <= 2000} label={`字数: ${wc.toLocaleString()} 字`} detail={wc < 600 ? "内容偏短，建议 600-2000 字" : wc > 2000 ? "内容偏长，可考虑精简" : `阅读时间约 ${seo.reading_time_min ?? 0} 分钟`} />
        <CheckItem pass={cta} label={`CTA 行动号召: ${cta ? "有" : "无"}`} detail={cta ? "已包含行动号召" : "建议添加 CTA（如「立即注册」「开始使用」）"} />
        {kdEntries.length > 0 ? (
          <>
            <CheckItem
              pass={avgDensity >= 0.5 && avgDensity <= 3.0}
              label={`关键词密度: ${avgDensity.toFixed(2)}%`}
              detail={avgDensity < 0.5 ? "密度偏低，建议增加关键词使用" : avgDensity > 3.0 ? "密度偏高，有堆砌风险" : "密度适中"}
            />
            <div style={{ padding: "4px 0 4px 28px", fontSize: "0.82rem", color: "var(--muted)" }}>
              {kdEntries.map(([kw, v]) => (
                <span key={kw} style={{ display: "inline-block", marginRight: 16 }}>
                  <strong>{kw}</strong>: {v.count} 次 ({v.density_pct}%)
                </span>
              ))}
            </div>
          </>
        ) : (
          <CheckItem pass={false} label="关键词: 未设置" detail="请在「目标关键词」中输入关键词后重新分析" />
        )}
      </div>
    );
  }

  function renderGeoChecklist(geo: GeoData) {
    const d = geo.details ?? {};
    const issues = geo.issues ?? [];
    const tips = geo.tips ?? [];

    return (
      <div>
        <CheckItem
          pass={(d.answer_first_len ?? 0) >= 40 && (d.answer_first_len ?? 0) <= 200}
          label={`Answer-First 首段: ${d.answer_first_len ?? 0} 字`}
          detail={(d.answer_first_len ?? 0) >= 40 && (d.answer_first_len ?? 0) <= 200 ? "首段直接回答核心问题" : "首段应 40-200 字直接回答用户最可能的问题"}
        />
        <CheckItem
          pass={(d.question_h2_ratio ?? 0) >= 30}
          label={`问句式 H2: ${(d.question_h2_ratio ?? 0).toFixed(0)}%`}
          detail={(d.question_h2_ratio ?? 0) >= 30 ? "达到 30% 目标" : "建议至少 30% 的 H2 使用问句（如「XX 安全吗？」）"}
        />
        <CheckItem
          pass={(d.citation_count ?? 0) >= 5}
          label={`数据/统计引用: ${d.citation_count ?? 0} 处`}
          detail={(d.citation_count ?? 0) >= 5 ? "数据引用充足" : "建议添加更多带来源的统计数据（≥5 处）"}
        />
        <CheckItem
          pass={(d.long_paragraphs ?? 0) === 0}
          label={`段落长度: ${(d.long_paragraphs ?? 0) === 0 ? "全部达标" : `${d.long_paragraphs} 个超长段落`}`}
          detail={(d.long_paragraphs ?? 0) === 0 ? "所有段落 ≤300 字" : "有超长段落，建议拆分为 2-3 句一段"}
        />
        <CheckItem
          pass={(d.faq_count ?? 0) >= 3}
          label={`FAQ 问答: ${d.faq_count ?? 0} 对`}
          detail={(d.faq_count ?? 0) >= 5 ? "FAQ 覆盖充足" : (d.faq_count ?? 0) >= 3 ? "建议补充到 5 对以获得最佳效果" : "建议在文末加入 3-5 个 FAQ 问答对"}
        />
        <CheckItem
          pass={(d.authority_refs ?? 0) >= 3}
          label={`权威来源引用: ${d.authority_refs ?? 0} 处`}
          detail={(d.authority_refs ?? 0) >= 3 ? "引用充足" : "建议使用「据 [权威机构] 研究显示」提升可信度"}
        />
        <CheckItem
          pass={(d.entity_mentions ?? 0) >= 3}
          label={`品牌实体提及: ${d.entity_mentions ?? 0}/4`}
          detail={(d.entity_mentions ?? 0) >= 3 ? "品牌曝光一致" : "建议在文中统一提及 MPChat / MP Card / MP Wallet / mp.net"}
        />
        {tips.length > 0 && (
          <div style={{ marginTop: 12, padding: "10px 12px", background: "rgba(99,91,255,0.08)", borderRadius: 8, fontSize: "0.85rem" }}>
            <strong style={{ color: "var(--accent)" }}>优化建议：</strong>
            <ul style={{ margin: "6px 0 0", paddingLeft: 18, lineHeight: 1.6 }}>
              {tips.map((tip, i) => <li key={i}>{tip}</li>)}
            </ul>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="page-shell">
      <section className="hero-card compact">
        <div>
          <span className="eyebrow">{t("nav.external")}</span>
          <h1>文章质量检测与 SEO/GEO 优化</h1>
          <p className="muted-text" style={{marginTop:4,fontSize:"0.9rem"}}>粘贴 AI 生成的文章，一键检查 SEO 规范、GEO 适配度和 AI 痕迹</p>
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
            <textarea rows={16} value={article} onChange={(e) => setArticle(e.target.value)} placeholder="粘贴需要检查的文章内容（Markdown 格式）..." />
          </label>
        </div>

        {article.trim() && (
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", padding: "8px 0", fontSize: "0.82rem", color: "var(--muted)", borderTop: "1px solid rgba(255,255,255,0.06)", marginTop: 8 }}>
            <span>{wordStats.total.toLocaleString()} 字</span>
            <span>约 {Math.max(1, Math.ceil(wordStats.total / 300))} 分钟阅读</span>
            {wordStats.cn > 0 && <span>中文 {wordStats.cn.toLocaleString()}</span>}
            {wordStats.en > 0 && <span>英文 {wordStats.en.toLocaleString()}</span>}
            {Object.keys(kwOccurrences).length > 0 && (
              <span style={{ borderLeft: "1px solid rgba(255,255,255,0.1)", paddingLeft: 12 }}>
                关键词：{Object.entries(kwOccurrences).map(([kw, c]) => `${kw}(${c})`).join("、")}
              </span>
            )}
          </div>
        )}

        <div className="form-grid" style={{ marginTop: 8 }}>
          <label className="span-4">
            <span>{t("form.targetKeywords")}</span>
            <textarea rows={2} value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="输入目标关键词，用逗号分隔（如 MPChat, 加密支付, 数字钱包）" />
          </label>
        </div>

        <div className="action-row" style={{marginTop:12}}>
          <button className="primary-button" onClick={handleAnalyze} disabled={loading || !article.trim()}>
            {btnLabel("analyze", t("btn.analyze"))}
          </button>
          <button className="secondary-button" onClick={() => handleOptimize("seo")} disabled={loading || !aiCfg.api_key.trim() || !article.trim()}>{btnLabel("seo", t("btn.optimizeSeo"))}</button>
          <button className="secondary-button" onClick={() => handleOptimize("geo")} disabled={loading || !aiCfg.api_key.trim() || !article.trim()}>{btnLabel("geo", t("btn.optimizeGeo"))}</button>
          <button className="secondary-button" onClick={() => handleOptimize("dual")} disabled={loading || !aiCfg.api_key.trim() || !article.trim()}>{btnLabel("dual", t("btn.optimizeDual"))}</button>
          <button className="primary-button" onClick={() => handleOptimize("triple")} disabled={loading || !aiCfg.api_key.trim() || !article.trim()} style={!loading ? {background:"linear-gradient(135deg,#ff6b81,#7c8cff)"} : {}}>{btnLabel("triple", t("btn.optimizeTriple"))}</button>
          <button className="secondary-button" onClick={() => handleOptimize("humanize")} disabled={loading || !aiCfg.api_key.trim() || !article.trim()}>{btnLabel("humanize", t("btn.humanize"))}</button>
          <button className="secondary-button" onClick={handleDetectAi} disabled={loading || !aiCfg.api_key.trim() || !article.trim()}>{btnLabel("detect", t("btn.detectAi"))}</button>
        </div>

        {loading && progressStage && (
          <div className="warmup-banner" style={{ marginTop: 8 }}>
            <span>{stageLabels[progressStage] || "处理中..."}</span>
          </div>
        )}
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
            <div style={{flex:1}}>
              <div className="rendered-article" style={{fontSize:"0.9rem"}}><ReactMarkdown remarkPlugins={[remarkGfm]}>{aiDetect.summary}</ReactMarkdown></div>
            </div>
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
            <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 16 }}>
              <ScoreRing score={analysis.seo?.structure_score ?? 0} label="SEO" size={80} />
              <div>
                <h2 style={{ margin: 0 }}>SEO 检查</h2>
                <p className="muted-text" style={{ margin: "4px 0 0", fontSize: "0.85rem" }}>搜索引擎优化规范检查</p>
              </div>
            </div>
            {renderSeoChecklist(analysis.seo ?? {})}
          </div>
          <div className="glass-card">
            <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 16 }}>
              <ScoreRing score={analysis.geo?.score ?? 0} label="GEO" size={80} />
              <div>
                <h2 style={{ margin: 0 }}>GEO 检查</h2>
                <p className="muted-text" style={{ margin: "4px 0 0", fontSize: "0.85rem" }}>AI 搜索引擎适配度检查</p>
              </div>
            </div>
            {renderGeoChecklist(analysis.geo ?? {})}
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
          <ul className="plain-list" style={{marginTop:12}}>{(optimized.changelog ?? []).map((item, i) => (<li key={i}>{item}</li>))}</ul>
        </section>
      ) : null}

      {article.trim() && (
        <section className="glass-card">
          <div className="section-header" style={{marginBottom: translatedArticle ? 12 : 0}}>
            <h3 style={{fontSize:"1rem",margin:0}}>{t("label.translate")}</h3>
            <div className="action-row">
              <button
                className="secondary-button"
                onClick={() => handleTranslateExternal("英文 (English)")}
                disabled={loading || !aiCfg.api_key.trim()}
              >
                {loadingAction === "translate" && translateTarget === "英文 (English)"
                  ? t("btn.translating")
                  : t("btn.translateToEn")}
              </button>
              <button
                className="secondary-button"
                onClick={() => handleTranslateExternal("繁体中文 (Traditional Chinese)")}
                disabled={loading || !aiCfg.api_key.trim()}
              >
                {loadingAction === "translate" && translateTarget === "繁体中文 (Traditional Chinese)"
                  ? t("btn.translating")
                  : t("btn.translateToTw")}
              </button>
            </div>
          </div>
          {translatedArticle && (
            <details open={translateOpen} onToggle={(e) => setTranslateOpen((e.target as HTMLDetailsElement).open)}>
              <summary className="collapse-header">{t("label.translateResult")} — {translateTarget}</summary>
              <div style={{marginTop:12}}>
                <div className="action-row" style={{marginBottom:8}}>
                  <button className="secondary-button" onClick={() => doCopy(translatedArticle)}>{t("btn.copyTranslation")}</button>
                  <button className="secondary-button" onClick={() => downloadFile(translatedArticle, `translated-${translateTarget}.md`, "text/markdown")}>{t("btn.downloadTranslation")}</button>
                </div>
                <div className="article-card rendered-article"><ReactMarkdown remarkPlugins={[remarkGfm]}>{translatedArticle}</ReactMarkdown></div>
              </div>
            </details>
          )}
        </section>
      )}
    </div>
  );
}
