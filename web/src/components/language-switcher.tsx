"use client";

import { useState, useRef, useEffect } from "react";
import { useLanguage, type Locale } from "@/context/language-context";
import { ChevronDown } from "lucide-react";

export function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { locale, setLocale, locales, labels, flags } = useLanguage();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((p) => !p)}
        className="flex items-center gap-1.5 rounded-xl border border-[#ebebeb] bg-white px-3 py-1.5 text-sm font-semibold text-[#444444] shadow-sm hover:border-[#b0b0b0] hover:bg-[#f7f7f7] transition-all"
        aria-label="Change language"
      >
        <span>{flags[locale]}</span>
        {!compact && <span>{labels[locale]}</span>}
        <ChevronDown className={`h-3.5 w-3.5 text-[#b0b0b0] transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1.5 w-36 rounded-2xl border border-[#ebebeb] bg-white py-1.5 shadow-[0_8px_24px_rgba(0,0,0,0.12)] z-50">
          {locales.map((l) => (
            <button
              key={l}
              onClick={() => { setLocale(l as Locale); setOpen(false); }}
              className={`flex w-full items-center gap-2.5 px-4 py-2 text-sm transition-colors ${
                l === locale
                  ? "font-bold text-[#ff385c] bg-[#fff0f2]"
                  : "font-medium text-[#444444] hover:bg-[#f7f7f7]"
              }`}
            >
              <span>{flags[l as Locale]}</span>
              <span>{labels[l as Locale]}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
