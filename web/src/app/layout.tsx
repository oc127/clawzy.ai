import { getLocale } from "next-intl/server";
import { getTranslations } from "next-intl/server";
import "./globals.css";

export async function generateMetadata() {
  const t = await getTranslations("metadata");
  return {
    title: t("title"),
    description: t("description"),
    metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || "https://clawzy.ai"),
    openGraph: {
      title: t("title"),
      description: t("description"),
      siteName: "Clawzy.ai",
      type: "website",
      url: process.env.NEXT_PUBLIC_APP_URL || "https://clawzy.ai",
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
        "zh-CN": `${process.env.NEXT_PUBLIC_APP_URL || "https://clawzy.ai"}/zh-CN`,
        "en": `${process.env.NEXT_PUBLIC_APP_URL || "https://clawzy.ai"}/en`,
        "ja": `${process.env.NEXT_PUBLIC_APP_URL || "https://clawzy.ai"}/ja`,
        "ko": `${process.env.NEXT_PUBLIC_APP_URL || "https://clawzy.ai"}/ko`,
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
