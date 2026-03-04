import { getLocale } from "next-intl/server";
import { getTranslations } from "next-intl/server";
import "./globals.css";

export async function generateMetadata() {
  const t = await getTranslations("metadata");
  return {
    title: t("title"),
    description: t("description"),
    metadataBase: new URL("https://clawzy.ai"),
    openGraph: {
      title: t("title"),
      description: t("description"),
      siteName: "Clawzy.ai",
      type: "website",
      url: "https://clawzy.ai",
      images: [{ url: "/og-image.png", width: 1200, height: 630 }],
    },
    twitter: {
      card: "summary_large_image",
      title: t("title"),
      description: t("description"),
      images: ["/og-image.png"],
    },
    icons: { icon: "/favicon.ico" },
    alternates: {
      languages: {
        "zh-CN": "https://clawzy.ai",
        "en": "https://clawzy.ai",
        "ja": "https://clawzy.ai",
        "ko": "https://clawzy.ai",
      },
    },
  };
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getLocale();

  return (
    <html lang={locale}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
