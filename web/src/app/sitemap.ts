import type { MetadataRoute } from "next";

const BASE_URL = "https://clawzy.ai";

export default function sitemap(): MetadataRoute.Sitemap {
  const locales = ["en", "zh", "ja", "ko"];

  const pages = [
    { path: "", priority: 1.0, changeFrequency: "weekly" as const },
    { path: "/login", priority: 0.5, changeFrequency: "monthly" as const },
    { path: "/register", priority: 0.5, changeFrequency: "monthly" as const },
    { path: "/terms", priority: 0.3, changeFrequency: "yearly" as const },
    { path: "/privacy", priority: 0.3, changeFrequency: "yearly" as const },
  ];

  return locales.flatMap((locale) =>
    pages.map((page) => ({
      url: `${BASE_URL}/${locale}${page.path}`,
      lastModified: new Date(),
      changeFrequency: page.changeFrequency,
      priority: page.priority,
    })),
  );
}
