"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { forgotPassword } from "@/lib/api";

const inputClass =
  "w-full px-4 py-2.5 bg-surface border border-border rounded-lg text-foreground placeholder-muted text-sm focus:outline-none focus:border-accent transition-colors";

export default function ForgotPasswordPage() {
  const t = useTranslations("auth");
  const tc = useTranslations("common");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await forgotPassword(email);
      setSuccess(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("sendFailed"));
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="w-full max-w-sm space-y-6 text-center">
          <h1 className="text-base font-semibold text-foreground tracking-tight">Clawzy</h1>
          <h2 className="text-xl font-semibold text-foreground">{t("emailSent")}</h2>
          <p className="text-sm text-muted">{t("emailSentDesc")}</p>
          <Link href="/login" className="inline-block text-sm text-accent hover:text-accent-hover transition-colors">
            {tc("backToLogin")}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center">
          <h1 className="text-base font-semibold text-foreground tracking-tight">Clawzy</h1>
          <h2 className="mt-6 text-xl font-semibold text-foreground">{t("forgotPasswordTitle")}</h2>
          <p className="mt-1.5 text-sm text-muted">{t("forgotPasswordDesc")}</p>
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

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {loading ? t("sending") : t("sendResetLink")}
          </button>
        </form>

        <p className="text-center text-muted text-sm">
          {t("remembered")}{" "}
          <Link href="/login" className="text-accent hover:text-accent-hover transition-colors">
            {tc("backToLogin")}
          </Link>
        </p>
      </div>
    </div>
  );
}
