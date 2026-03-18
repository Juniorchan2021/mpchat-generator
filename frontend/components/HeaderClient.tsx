"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { useI18n } from "@/lib/i18n";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function HeaderClient() {
  const { t, locale, setLocale } = useI18n();
  const pathname = usePathname();

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/health`).catch(() => {});
  }, []);

  return (
    <header className="topbar">
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <img
          src="https://mp.net/Logo.png"
          alt="MPChat Logo"
          style={{ height: 32, objectFit: "contain" }}
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
        />
        <span className="eyebrow">MPChat</span>
        <strong className="brand-title">{t("nav.brand")}</strong>
      </div>
      <nav className="nav-pills">
        <Link href="/" className={pathname === "/" ? "active" : ""}>
          {t("nav.workspace")}
        </Link>
        <Link href="/external" className={pathname === "/external" ? "active" : ""}>
          {t("nav.external")}
        </Link>
        <Link href="/history" className={pathname === "/history" ? "active" : ""}>
          {t("nav.history")}
        </Link>
        <Link href="/ideation" className={pathname === "/ideation" ? "active" : ""}>
          {t("nav.ideation")}
        </Link>
        <Link href="/intercom-qa" className={pathname === "/intercom-qa" ? "active" : ""}>
          {t("nav.intercomQA")}
        </Link>
        <button
          className="lang-toggle"
          onClick={() => setLocale(locale === "zh" ? "en" : "zh")}
        >
          {locale === "zh" ? "EN" : "中"}
        </button>
      </nav>
    </header>
  );
}
