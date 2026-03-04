"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { login } from "@/lib/api";

const inputClass =
  "w-full px-4 py-2.5 bg-surface border border-border rounded-lg text-foreground placeholder-muted text-sm focus:outline-none focus:border-accent transition-colors";

export default function LoginPage() {
  const router = useRouter();
  const t = useTranslations("auth");
  const tc = useTranslations("common");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login(email, password);
      localStorage.setItem("token", res.access_token);
      localStorage.setItem("refresh_token", res.refresh_token);
      router.push("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("loginFailed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center">
          <h1 className="text-base font-semibold text-foreground tracking-tight">Clawzy</h1>
          <h2 className="mt-6 text-xl font-semibold text-foreground">{t("welcomeBack")}</h2>
          <p className="mt-1.5 text-sm text-muted">{t("lobsterWaiting")}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {error && (
            <div className="border border-red-500/30 text-red-400 rounded-lg px-3 py-2.5 text-sm">
              {error}
            </div>
          )}

          <input
            type="email"
            placeholder={t("email")}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className={inputClass}
          />
          <input
            type="password"
            placeholder={t("password")}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className={inputClass}
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {loading ? t("loggingIn") : tc("login")}
          </button>

          <div className="text-right">
            <Link href="/forgot-password" className="text-xs text-muted hover:text-accent transition-colors">
              {t("forgotPassword")}
            </Link>
          </div>
        </form>

        <p className="text-center text-muted text-sm">
          {t("noAccount")}{" "}
          <Link href="/register" className="text-accent hover:text-accent-hover transition-colors">
            {tc("register")}
          </Link>
        </p>
      </div>
    </div>
  );
}
