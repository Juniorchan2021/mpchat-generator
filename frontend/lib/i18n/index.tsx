"use client";
import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import zh from "./zh.json";
import en from "./en.json";

type Locale = "zh" | "en";
const dictionaries: Record<Locale, Record<string, string>> = { zh, en };

interface I18nCtx {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nCtx>({
  locale: "zh",
  setLocale: () => {},
  t: (k) => k,
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("mpchat-locale"); return stored === "zh" || stored === "en" ? stored : "zh";
    }
    return "zh";
  });

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    localStorage.setItem("mpchat-locale", l);
  }, []);

  const t = useCallback(
    (key: string) => dictionaries[locale][key] ?? key,
    [locale],
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export const useI18n = () => useContext(I18nContext);
