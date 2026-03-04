"use client";

import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { useTransition } from "react";

const LOCALE_LABELS: Record<string, string> = {
  zh: "中文",
  en: "EN",
  ja: "日本語",
  ko: "한국어",
};

const LOCALES = ["zh", "en", "ja", "ko"] as const;

export default function LanguageSwitcher({ className }: { className?: string }) {
  const locale = useLocale();
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function handleChange(newLocale: string) {
    document.cookie = `locale=${newLocale};path=/;max-age=${365 * 24 * 60 * 60};samesite=lax`;
    startTransition(() => {
      router.refresh();
    });
  }

  return (
    <select
      value={locale}
      onChange={(e) => handleChange(e.target.value)}
      disabled={isPending}
      className={`bg-transparent border border-border text-muted text-xs rounded-md px-2 py-1.5 focus:outline-none cursor-pointer hover:text-foreground transition-colors ${className || ""}`}
    >
      {LOCALES.map((loc) => (
        <option key={loc} value={loc} className="bg-surface text-foreground">
          {LOCALE_LABELS[loc]}
        </option>
      ))}
    </select>
  );
}
