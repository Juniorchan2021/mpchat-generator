"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { clearHistory, readHistory } from "@/lib/history";
import { useI18n } from "@/lib/i18n";
import type { HistoryItem } from "@/lib/types";

const LOAD_KEY = "mpchat-load-workspace";

export function HistoryClient() {
  const { t } = useI18n();
  const [items, setItems] = useState<HistoryItem[]>(() => readHistory());
  const router = useRouter();

  function handleClear() {
    clearHistory();
    setItems([]);
  }

  function handleLoadToWorkspace(item: HistoryItem) {
    window.localStorage.setItem(LOAD_KEY, JSON.stringify(item));
    router.push("/");
  }

  return (
    <div className="page-shell">
      <section className="hero-card compact">
        <div>
          <span className="eyebrow">{t("nav.history")}</span>
          <h1>{t("nav.history")}</h1>
          
        </div>
        <button className="secondary-button" onClick={handleClear}>
          {t("btn.clear")}
        </button>
      </section>

      <section className="stack-column">
        {items.length === 0 ? (
          <div className="glass-card">
            <h2>{t("empty.history")}</h2>
            
          </div>
        ) : null}

        {items.map((item) => (
          <article className="glass-card" key={item.id}>
            <div className="section-header">
              <div>
                <h2>{item.result.title}</h2>
                <p>{item.scenario} · {new Date(item.createdAt).toLocaleString()}</p>
              </div>
              <div className="score-strip">
                <div className="score-card"><span>SEO</span><strong>{item.seoScore}</strong></div>
                <div className="score-card"><span>GEO</span><strong>{item.geoScore}</strong></div>
              </div>
            </div>
            <p className="muted-text">{item.result.meta_description}</p>
            <pre className="article-card clamp-article">{item.result.article}</pre>
            <div className="action-row" style={{marginTop:10}}>
              <button className="primary-button" onClick={() => handleLoadToWorkspace(item)} style={{padding:"8px 14px",fontSize:"0.85rem"}}>
                {t("btn.loadToWorkspace")}
              </button>
              {item.result.ab_titles && item.result.ab_titles.length > 0 && (
                <div className="pill-row">
                  <span className="subtle-label">A/B 标题:</span>
                  {item.result.ab_titles.map((alt) => (
                    <span className="pill" key={alt}>{alt}</span>
                  ))}
                </div>
              )}
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
