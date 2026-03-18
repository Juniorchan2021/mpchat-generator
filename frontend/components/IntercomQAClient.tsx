"use client";

import { useState, useEffect, useMemo, useRef } from "react";

import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { loadAiConfig, saveAiConfig, type AiConfig } from "@/lib/aiConfig";
import { FALLBACK_CONFIG } from "@/lib/fallbackConfig";
import type { IntercomCollection, Provider, QAPair } from "@/lib/types";

const QA_CACHE_KEY = "mpchat-intercom-qa-cache";

const LANGUAGE_TABS = [
  { key: "zh", label: "简体中文" },
  { key: "zh-TW", label: "繁體中文" },
  { key: "en", label: "English" },
];

const LOCALE_MAP: Record<string, string> = {
  "zh": "zh",
  "zh-TW": "zh-TW",
  "en": "en",
};

function getCollectionName(col: IntercomCollection, lang: string): string {
  if (col.translated_content[lang]) return col.translated_content[lang];
  if (col.translated_content["en"]) return col.translated_content["en"];
  return col.name;
}

export function IntercomQAClient() {
  const { t } = useI18n();
  const DEFAULT_GEMINI_KEY = process.env.NEXT_PUBLIC_DEFAULT_GEMINI_KEY || "";

  const [providers, setProviders] = useState<Provider[]>(FALLBACK_CONFIG.providers);
  const [aiCfg, setAiCfg] = useState<AiConfig>({
    provider: "gemini",
    model: "gemini-2.5-flash",
    api_key: DEFAULT_GEMINI_KEY,
    base_url: "https://generativelanguage.googleapis.com/v1beta/openai/",
  });
  const [configExpanded, setConfigExpanded] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  // 输入字段
  const [featureDescription, setFeatureDescription] = useState("");
  const [productName, setProductName] = useState("MPChat");
  const [count, setCount] = useState(10);

  // 多语言 QA 结果：按语言分组
  const [qaByLanguage, setQaByLanguage] = useState<Record<string, QAPair[]>>({});
  const [editedByLanguage, setEditedByLanguage] = useState<Record<string, QAPair[]>>({});
  const [activeTab, setActiveTab] = useState("zh");

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [showWarmup, setShowWarmup] = useState(false);

  // Intercom 配置
  const [intercomToken, setIntercomToken] = useState("");
  const [showIntercomToken, setShowIntercomToken] = useState(false);

  // Collections（从 Intercom 读取）
  const [collections, setCollections] = useState<IntercomCollection[]>([]);
  const [isFetchingCollections, setIsFetchingCollections] = useState(false);
  const [collectionsError, setCollectionsError] = useState("");

  // 每个语言选中的 collection id
  const [selectedCollectionIds, setSelectedCollectionIds] = useState<Record<string, string>>({
    "zh": "",
    "zh-TW": "",
    "en": "",
  });

  const [uploadingLang, setUploadingLang] = useState<string | null>(null);
  const [uploadingIdx, setUploadingIdx] = useState<number | null>(null);
  const [uploadResults, setUploadResults] = useState<Record<string, Record<number, { ok: boolean; url: string; error?: string }>>>({});

  const resultRef = useRef<HTMLDivElement>(null);

  // 加载 providers + AI 配置 + 缓存
  useEffect(() => {
    api.getConfig().then((data) => {
      if (data.providers?.length) setProviders(data.providers);
    }).catch(() => { /* 保持 fallback */ });

    const saved = loadAiConfig();
    if (saved && saved.api_key) setAiCfg(saved);

    try {
      const cache = window.localStorage.getItem(QA_CACHE_KEY);
      if (cache) {
        const parsed = JSON.parse(cache);
        if (parsed.qaByLanguage && typeof parsed.qaByLanguage === "object") {
          setQaByLanguage(parsed.qaByLanguage);
          setEditedByLanguage(parsed.qaByLanguage);
          if (parsed.featureDescription) setFeatureDescription(parsed.featureDescription);
          if (parsed.productName) setProductName(parsed.productName);
        }
      }
    } catch { /* noop */ }
  }, []);

  // 持久化 AI 配置
  useEffect(() => {
    if (aiCfg.provider && aiCfg.api_key) saveAiConfig(aiCfg);
  }, [aiCfg.provider, aiCfg.model, aiCfg.api_key, aiCfg.base_url]);

  // 错误/成功消息自动消失
  useEffect(() => {
    if (!error) return;
    const timer = setTimeout(() => setError(""), 8000);
    return () => clearTimeout(timer);
  }, [error]);

  useEffect(() => {
    if (!successMsg) return;
    const timer = setTimeout(() => setSuccessMsg(""), 5000);
    return () => clearTimeout(timer);
  }, [successMsg]);

  const currentProvider = useMemo(
    () => providers.find((p) => p.id === aiCfg.provider),
    [providers, aiCfg.provider],
  );

  function handleProviderChange(providerId: string) {
    const p = providers.find((x) => x.id === providerId);
    const newKey = providerId === "gemini" ? DEFAULT_GEMINI_KEY : "";
    setAiCfg((prev) => ({
      ...prev,
      provider: providerId,
      model: p?.models?.[0] || "",
      base_url: p?.base_url || "",
      api_key: newKey || prev.api_key,
    }));
  }

  async function handleFetchCollections() {
    if (!intercomToken.trim()) {
      setCollectionsError(t("intercom.err.noToken"));
      return;
    }
    setIsFetchingCollections(true);
    setCollectionsError("");
    try {
      const resp = await api.getIntercomCollections(intercomToken.trim());
      setCollections(resp.collections);
      if (resp.collections.length === 0) {
        setCollectionsError(t("intercom.err.noCollections"));
      }
    } catch (e) {
      setCollectionsError(e instanceof Error ? e.message : t("err.requestFailed"));
    } finally {
      setIsFetchingCollections(false);
    }
  }

  async function handleGenerate() {
    if (!featureDescription.trim()) {
      setError(t("intercom.err.noDescription"));
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
      setQaByLanguage({});
      setEditedByLanguage({});
      setUploadResults({});

      const resp = await api.generateIntercomQA({
        provider: aiCfg.provider,
        api_key: aiCfg.api_key,
        base_url: aiCfg.base_url,
        model: aiCfg.model,
        feature_description: featureDescription.trim(),
        product_name: productName.trim(),
        tone: "friendly",
        count,
        languages: ["zh", "zh-TW", "en"],
      });

      setQaByLanguage(resp.qa_by_language);
      setEditedByLanguage(resp.qa_by_language);

      const totalCount = Object.values(resp.qa_by_language).reduce((s, a) => s + a.length, 0);
      if (totalCount === 0) {
        setError(t("intercom.msg.noQA"));
      } else {
        try {
          window.localStorage.setItem(
            QA_CACHE_KEY,
            JSON.stringify({
              qaByLanguage: resp.qa_by_language,
              featureDescription: featureDescription.trim(),
              productName: productName.trim(),
            }),
          );
        } catch { /* noop */ }
        setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : t("err.requestFailed"));
    } finally {
      clearTimeout(warmupTimer);
      setShowWarmup(false);
      setIsLoading(false);
    }
  }

  function handleEditPair(lang: string, idx: number, field: keyof QAPair, value: string) {
    setEditedByLanguage((prev) => {
      const langPairs = [...(prev[lang] || [])];
      langPairs[idx] = { ...langPairs[idx], [field]: value };
      return { ...prev, [lang]: langPairs };
    });
  }

  function handleDeletePair(lang: string, idx: number) {
    setEditedByLanguage((prev) => ({
      ...prev,
      [lang]: (prev[lang] || []).filter((_, i) => i !== idx),
    }));
  }

  function exportMarkdown(lang: string) {
    const pairs = editedByLanguage[lang] || [];
    const langLabel = LANGUAGE_TABS.find((tab) => tab.key === lang)?.label || lang;
    const categories = Array.from(new Set(pairs.map((p) => p.category)));
    const lines: string[] = [`# ${productName} Help Center Q&A — ${langLabel}\n`];
    for (const cat of categories) {
      lines.push(`## ${cat}\n`);
      for (const pair of pairs.filter((p) => p.category === cat)) {
        lines.push(`### ${pair.question}\n`);
        lines.push(`${pair.answer}\n`);
      }
    }
    const blob = new Blob([lines.join("\n")], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${productName.toLowerCase().replace(/\s+/g, "-")}-qa-${lang}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function exportJson(lang: string) {
    const pairs = editedByLanguage[lang] || [];
    const blob = new Blob([JSON.stringify(pairs, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${productName.toLowerCase().replace(/\s+/g, "-")}-qa-${lang}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleUploadOne(lang: string, idx: number) {
    if (!intercomToken.trim()) {
      setError(t("intercom.err.noToken"));
      return;
    }
    const pair = (editedByLanguage[lang] || [])[idx];
    if (!pair) return;

    setUploadingLang(lang);
    setUploadingIdx(idx);
    try {
      const resp = await api.uploadToIntercom({
        intercom_token: intercomToken.trim(),
        collection_id: selectedCollectionIds[lang]?.trim() || "",
        title: pair.question,
        body: pair.answer,
        locale: LOCALE_MAP[lang] || lang,
      });
      setUploadResults((prev) => ({
        ...prev,
        [lang]: { ...(prev[lang] || {}), [idx]: { ok: resp.ok, url: resp.url } },
      }));
    } catch (e) {
      setUploadResults((prev) => ({
        ...prev,
        [lang]: {
          ...(prev[lang] || {}),
          [idx]: { ok: false, url: "", error: e instanceof Error ? e.message : t("err.requestFailed") },
        },
      }));
    } finally {
      setUploadingLang(null);
      setUploadingIdx(null);
    }
  }

  async function handleUploadAll(lang: string) {
    if (!intercomToken.trim()) {
      setError(t("intercom.err.noToken"));
      return;
    }
    const pairs = editedByLanguage[lang] || [];
    for (let i = 0; i < pairs.length; i++) {
      await handleUploadOne(lang, i);
    }
    setSuccessMsg(t("intercom.msg.uploadLangDone").replace("{lang}", LANGUAGE_TABS.find((tab) => tab.key === lang)?.label || lang));
  }

  const hasResults = Object.values(editedByLanguage).some((arr) => arr.length > 0);
  const modelOptions = currentProvider?.models ?? [];
  const activePairs = editedByLanguage[activeTab] || [];
  const activeCategories = Array.from(new Set(activePairs.map((p) => p.category)));

  return (
    <div className="workspace-layout" style={{ maxWidth: 960, margin: "0 auto" }}>
      {/* ── AI 配置面板 ── */}
      <section className="glass-card">
        <div className="section-header" style={{ marginBottom: configExpanded ? 16 : 0 }}>
          <h2 style={{ margin: 0 }}>{t("intercom.title")}</h2>
          <button
            className="secondary-button"
            onClick={() => setConfigExpanded((v) => !v)}
            style={{ padding: "4px 12px", fontSize: "0.82rem" }}
          >
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
                  placeholder="输入模型名称"
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
        <h2>{t("intercom.inputTitle")}</h2>
        <div className="form-grid">
          <label className="span-4">
            <span>{t("intercom.featureDescription")}</span>
            <textarea
              rows={5}
              placeholder={t("intercom.featureDescriptionPlaceholder")}
              value={featureDescription}
              onChange={(e) => setFeatureDescription(e.target.value)}
              style={{ resize: "vertical", fontFamily: "inherit" }}
            />
          </label>
          <label className="span-2">
            <span>{t("intercom.productName")}</span>
            <input
              placeholder="MPChat"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
            />
          </label>
          <label className="span-2">
            <span>{t("intercom.count")} — {count}</span>
            <input
              type="range"
              min={3}
              max={30}
              step={1}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              style={{ width: "100%", marginTop: 6 }}
            />
          </label>
        </div>

        <p className="muted-text" style={{ fontSize: "0.8rem", marginTop: 8, marginBottom: 0 }}>
          {t("intercom.multilangHint")}
        </p>

        <div className="action-row" style={{ marginTop: 12 }}>
          <button className="primary-button" onClick={handleGenerate} disabled={isLoading}>
            {isLoading ? t("intercom.generating") : t("intercom.generate")}
          </button>
          {hasResults && (
            <span className="muted-text" style={{ fontSize: "0.85rem" }}>
              {LANGUAGE_TABS.map((lang) => (
                <span key={lang.key} style={{ marginRight: 12 }}>
                  {lang.label}: {(editedByLanguage[lang.key] || []).length} 条
                </span>
              ))}
            </span>
          )}
        </div>

        {showWarmup && (
          <p className="muted-text" style={{ marginTop: 8, fontSize: "0.82rem" }}>{t("msg.serverWarmup")}</p>
        )}
        {error && (
          <p style={{ color: "var(--danger)", marginTop: 8, fontSize: "0.85rem" }}>{error}</p>
        )}
        {successMsg && (
          <p style={{ color: "var(--success)", marginTop: 8, fontSize: "0.85rem" }}>{successMsg}</p>
        )}
      </section>

      {/* ── 多语言结果面板 ── */}
      {hasResults && (
        <section className="glass-card" ref={resultRef}>
          {/* Tab 导航 */}
          <div style={{ display: "flex", gap: 4, marginBottom: 20, borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: 0 }}>
            {LANGUAGE_TABS.map((tab) => {
              const tabCount = (editedByLanguage[tab.key] || []).length;
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  style={{
                    padding: "8px 20px",
                    background: "none",
                    border: "none",
                    borderBottom: isActive ? "2px solid var(--primary)" : "2px solid transparent",
                    color: isActive ? "var(--primary)" : "var(--muted)",
                    cursor: "pointer",
                    fontSize: "0.88rem",
                    fontWeight: isActive ? 600 : 400,
                    transition: "all 0.15s",
                    marginBottom: -1,
                  }}
                >
                  {tab.label}
                  <span style={{ marginLeft: 6, fontSize: "0.75rem", opacity: 0.7 }}>({tabCount})</span>
                </button>
              );
            })}
            <div style={{ flex: 1 }} />
            <button className="secondary-button" onClick={() => exportMarkdown(activeTab)} style={{ padding: "5px 10px", fontSize: "0.78rem", alignSelf: "center" }}>
              {t("intercom.exportMd")}
            </button>
            <button className="secondary-button" onClick={() => exportJson(activeTab)} style={{ padding: "5px 10px", fontSize: "0.78rem", alignSelf: "center", marginLeft: 6 }}>
              {t("intercom.exportJson")}
            </button>
          </div>

          {/* QA 列表 */}
          {activeCategories.map((cat) => (
            <div key={cat} style={{ marginBottom: 20 }}>
              <h3 style={{ fontSize: "0.85rem", color: "var(--primary)", marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                {cat}
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {activePairs.map((pair, idx) => {
                  if (pair.category !== cat) return null;
                  const uploadResult = (uploadResults[activeTab] || {})[idx];
                  const isUploading = uploadingLang === activeTab && uploadingIdx === idx;
                  return (
                    <div key={idx} className="article-card" style={{ padding: "14px 16px" }}>
                      {/* 问题行 */}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8, marginBottom: 8 }}>
                        <input
                          value={pair.question}
                          onChange={(e) => handleEditPair(activeTab, idx, "question", e.target.value)}
                          style={{ flex: 1, fontWeight: 600, background: "transparent", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, padding: "6px 10px", color: "inherit", fontSize: "0.92rem" }}
                          placeholder={t("intercom.questionPlaceholder")}
                        />
                        <button
                          onClick={() => handleDeletePair(activeTab, idx)}
                          style={{ background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: "1rem", padding: "4px 6px", flexShrink: 0 }}
                          title={t("intercom.deleteQA")}
                        >
                          ✕
                        </button>
                      </div>
                      {/* 回答框（纯文本） */}
                      <textarea
                        value={pair.answer}
                        onChange={(e) => handleEditPair(activeTab, idx, "answer", e.target.value)}
                        rows={3}
                        style={{ width: "100%", resize: "vertical", background: "transparent", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 6, padding: "6px 10px", color: "inherit", fontSize: "0.85rem", fontFamily: "inherit", boxSizing: "border-box" }}
                        placeholder={t("intercom.answerPlaceholder")}
                      />
                      {/* 底部操作栏 */}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
                        <select
                          value={pair.category}
                          onChange={(e) => handleEditPair(activeTab, idx, "category", e.target.value)}
                          style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, padding: "3px 8px", color: "inherit", fontSize: "0.78rem" }}
                        >
                          {activeCategories.map((c) => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                          {uploadResult && (
                            <span style={{ fontSize: "0.78rem", color: uploadResult.ok ? "var(--success)" : "var(--danger)" }}>
                              {uploadResult.ok
                                ? (uploadResult.url
                                    ? <a href={uploadResult.url} target="_blank" rel="noreferrer" style={{ color: "var(--success)" }}>{t("intercom.uploaded")}</a>
                                    : t("intercom.uploaded"))
                                : (uploadResult.error || t("intercom.uploadFailed"))
                              }
                            </span>
                          )}
                          <button
                            className="secondary-button"
                            onClick={() => handleUploadOne(activeTab, idx)}
                            disabled={isUploading || !intercomToken.trim()}
                            style={{ padding: "4px 10px", fontSize: "0.78rem" }}
                          >
                            {isUploading ? "..." : t("intercom.uploadOne")}
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </section>
      )}

      {/* ── Intercom 上传配置 ── */}
      {hasResults && (
        <section className="glass-card">
          <h2>{t("intercom.uploadTitle")}</h2>

          {/* Token 输入 + 读取 Collections 按钮 */}
          <div className="form-grid" style={{ marginBottom: 16 }}>
            <label className="span-4">
              <span>
                {t("intercom.intercomToken")}
                <a
                  href="https://app.intercom.com/a/apps/_/settings/access-tokens"
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: "var(--primary)", fontSize: "0.75rem", marginLeft: 6 }}
                >
                  获取
                </a>
              </span>
              <div style={{ display: "flex", gap: 8 }}>
                <div style={{ position: "relative", flex: 1 }}>
                  <input
                    type={showIntercomToken ? "text" : "password"}
                    placeholder={t("intercom.tokenPlaceholder")}
                    value={intercomToken}
                    onChange={(e) => setIntercomToken(e.target.value)}
                    style={{ paddingRight: 40, width: "100%" }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowIntercomToken((v) => !v)}
                    style={{ position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "var(--muted)", fontSize: "0.85rem", padding: 0 }}
                    title={showIntercomToken ? "隐藏" : "查看"}
                  >
                    {showIntercomToken ? "🙈" : "👁"}
                  </button>
                </div>
                <button
                  className="secondary-button"
                  onClick={handleFetchCollections}
                  disabled={isFetchingCollections || !intercomToken.trim()}
                  style={{ padding: "0 14px", fontSize: "0.82rem", whiteSpace: "nowrap", flexShrink: 0 }}
                >
                  {isFetchingCollections ? t("intercom.fetchingCollections") : t("intercom.fetchCollections")}
                </button>
              </div>
              {collectionsError && (
                <p style={{ color: "var(--danger)", fontSize: "0.8rem", marginTop: 4 }}>{collectionsError}</p>
              )}
              {collections.length > 0 && (
                <p className="muted-text" style={{ fontSize: "0.78rem", marginTop: 4 }}>
                  {t("intercom.collectionsLoaded").replace("{count}", String(collections.length))}
                </p>
              )}
            </label>
          </div>

          {/* 三语言 Collection 选择 + 批量上传 */}
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {LANGUAGE_TABS.map((lang) => {
              const pairs = editedByLanguage[lang.key] || [];
              const uploadedCount = Object.values(uploadResults[lang.key] || {}).filter((r) => r.ok).length;
              return (
                <div key={lang.key} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", background: "rgba(255,255,255,0.03)", borderRadius: 8, border: "1px solid rgba(255,255,255,0.07)" }}>
                  <span style={{ width: 90, fontSize: "0.85rem", fontWeight: 600, flexShrink: 0 }}>
                    {lang.label}
                  </span>
                  {collections.length > 0 ? (
                    <select
                      value={selectedCollectionIds[lang.key] || ""}
                      onChange={(e) => setSelectedCollectionIds((prev) => ({ ...prev, [lang.key]: e.target.value }))}
                      style={{ flex: 1, fontSize: "0.83rem", background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, padding: "6px 10px", color: "inherit" }}
                    >
                      <option value="">{t("intercom.selectCollection")}</option>
                      {collections.map((col) => (
                        <option key={col.id} value={col.id}>
                          {getCollectionName(col, lang.key)} (ID: {col.id})
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      placeholder={t("intercom.collectionIdPlaceholder")}
                      value={selectedCollectionIds[lang.key] || ""}
                      onChange={(e) => setSelectedCollectionIds((prev) => ({ ...prev, [lang.key]: e.target.value }))}
                      style={{ flex: 1, fontSize: "0.83rem" }}
                    />
                  )}
                  <span className="muted-text" style={{ fontSize: "0.78rem", flexShrink: 0 }}>
                    {uploadedCount}/{pairs.length}
                  </span>
                  <button
                    className="primary-button"
                    onClick={() => handleUploadAll(lang.key)}
                    disabled={uploadingLang !== null || !intercomToken.trim() || pairs.length === 0}
                    style={{ padding: "6px 14px", fontSize: "0.82rem", flexShrink: 0 }}
                  >
                    {uploadingLang === lang.key ? t("intercom.uploading") : t("intercom.uploadAll")}
                  </button>
                </div>
              );
            })}
          </div>

          <p className="muted-text" style={{ fontSize: "0.78rem", marginTop: 12 }}>
            {t("intercom.uploadHint")}
          </p>
        </section>
      )}
    </div>
  );
}
