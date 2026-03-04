import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["zh", "en", "ja", "ko"],
  defaultLocale: "zh",
  localePrefix: { mode: "never" },
  localeCookie: { name: "locale", sameSite: "lax" },
  localeDetection: true,
});

export type Locale = (typeof routing.locales)[number];
