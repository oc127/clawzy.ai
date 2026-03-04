import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Clawzy — 你的 AI 龙虾",
  description: "下载即用的 AI 助手，无需配置，开箱即聊",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh">
      <body className="antialiased">{children}</body>
    </html>
  );
}
