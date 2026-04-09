import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/auth-context";
import { LanguageProvider } from "@/context/language-context";
import { ThemeProvider } from "@/context/theme-context";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "NipponClaw — Your AI Agent, Any Brain.",
  description:
    "AI agent platform powered by multiple LLM models. Create custom agents, chat with any AI model, pay only for what you use.",
  icons: {
    icon: "/logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <ThemeProvider>
        <LanguageProvider>
          <AuthProvider>{children}</AuthProvider>
        </LanguageProvider>
        </ThemeProvider>
        <Toaster
          position="bottom-center"
          duration={4000}
          toastOptions={{
            style: {
              background: "#ffffff",
              border: "1px solid #dddddd",
              color: "#222222",
              boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
              borderRadius: "12px",
              fontFamily: "var(--font-jakarta), sans-serif",
            },
          }}
        />
      </body>
    </html>
  );
}
