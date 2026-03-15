"use client";

import { useState } from "react";

import { clearHistory, readHistory } from "@/lib/history";
import type { HistoryItem } from "@/lib/types";

export function HistoryClient() {
  const [items, setItems] = useState<HistoryItem[]>(() => readHistory());

  function handleClear() {
    clearHistory();
    setItems([]);
  }

  return (
    <div className="page-shell">
      <section className="hero-card compact">
        <div>
          <span className="eyebrow">History</span>
          <h1>生成历史</h1>
          <p>最近的生成结果保存在浏览器本地，可作为工作台的轻量回溯能力。</p>
        </div>
        <button className="secondary-button" onClick={handleClear}>
          清空历史
        </button>
      </section>

      <section className="stack-column">
        {items.length === 0 ? (
          <div className="glass-card">
            <h2>还没有历史记录</h2>
            <p>先回到工作台生成文章，随后这里会自动出现最近 50 条记录。</p>
          </div>
        ) : null}

        {items.map((item) => (
          <article className="glass-card" key={item.id}>
            <div className="section-header">
              <div>
                <h2>{item.result.title}</h2>
                <p>
                  {item.scenario} · {new Date(item.createdAt).toLocaleString()}
                </p>
              </div>
              <div className="score-strip">
                <div className="score-card">
                  <span>SEO</span>
                  <strong>{item.seoScore}</strong>
                </div>
                <div className="score-card">
                  <span>GEO</span>
                  <strong>{item.geoScore}</strong>
                </div>
              </div>
            </div>
            <p className="muted-text">{item.result.meta_description}</p>
            <pre className="article-card clamp-article">{item.result.article}</pre>
          </article>
        ))}
      </section>
    </div>
  );
}
