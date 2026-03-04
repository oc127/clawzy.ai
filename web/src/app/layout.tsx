import { getLocale } from "next-intl/server";
import { getTranslations } from "next-intl/server";
import "./globals.css";

export async function generateMetadata() {
  const t = await getTranslations("metadata");
  return {
    title: t("title"),
    description: t("description"),
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
