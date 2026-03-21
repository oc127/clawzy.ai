"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import en, { type Translations } from "@/lib/translations/en";
import zh from "@/lib/translations/zh";
import ja from "@/lib/translations/ja";
import ko from "@/lib/translations/ko";

export type Locale = "en" | "zh" | "ja" | "ko";

const LOCALE_LABELS: Record<Locale, string> = {
  en: "EN",
  zh: "中文",
  ja: "日本語",
  ko: "한국어",
};

const LOCALE_FLAGS: Record<Locale, string> = {
  en: "🇺🇸",
  zh: "🇨🇳",
  ja: "🇯🇵",
  ko: "🇰🇷",
};

const translations: Record<Locale, Translations> = { en, zh, ja, ko };

interface LanguageContextValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: Translations;
  locales: Locale[];
  labels: typeof LOCALE_LABELS;
  flags: typeof LOCALE_FLAGS;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

const STORAGE_KEY = "nc_locale";

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("ja");

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as Locale | null;
    if (saved && saved in translations) {
      setLocaleState(saved);
    } else {
      // Auto-detect from browser
      const lang = navigator.language.split("-")[0] as Locale;
      if (lang in translations) setLocaleState(lang);
    }
  }, []);

  const setLocale = (l: Locale) => {
    setLocaleState(l);
    localStorage.setItem(STORAGE_KEY, l);
  };

  return (
    <LanguageContext.Provider
      value={{
        locale,
        setLocale,
        t: translations[locale],
        locales: ["en", "zh", "ja", "ko"],
        labels: LOCALE_LABELS,
        flags: LOCALE_FLAGS,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}
