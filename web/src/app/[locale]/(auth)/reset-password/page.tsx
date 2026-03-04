"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { resetPassword } from "@/lib/api";

const inputClass =
  "w-full px-4 py-2.5 bg-surface border border-border rounded-lg text-foreground placeholder-muted text-sm focus:outline-none focus:border-accent transition-colors";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const t = useTranslations("auth");
  const tc = useTranslations("common");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="w-full max-w-sm space-y-6 text-center">
          <h1 className="text-base font-semibold text-foreground tracking-tight">Clawzy</h1>
          <h2 className="text-xl font-semibold text-foreground">{t("invalidLink")}</h2>
          <p className="text-sm text-muted">{t("invalidLinkDesc")}</p>
          <Link href="/forgot-password" className="inline-block text-sm text-accent hover:text-accent-hover transition-colors">
            {t("resendResetLink")}
          </Link>
        </div>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password.length < 6) {
      setError(t("passwordMinLength"));
      return;
    }
    if (password !== confirmPassword) {
      setError(t("passwordMismatch"));
      return;
    }

    setLoading(true);
    try {
      await resetPassword(token, password);
      router.push("/login");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("resetFailed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center">
          <h1 className="text-base font-semibold text-foreground tracking-tight">Clawzy</h1>
          <h2 className="mt-6 text-xl font-semibold text-foreground">{t("setNewPassword")}</h2>
          <p className="mt-1.5 text-sm text-muted">{t("enterNewPassword")}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {error && (
            <div className="border border-red-500/30 text-red-400 rounded-lg px-3 py-2.5 text-sm">
              {error}
            </div>
          )}

          <input
            type="password"
            placeholder={t("newPassword")}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            className={inputClass}
          />
          <input
            type="password"
            placeholder={t("confirmNewPassword")}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={6}
            className={inputClass}
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {loading ? t("resetting") : t("resetPassword")}
          </button>
        </form>

        <p className="text-center text-muted text-sm">
          <Link href="/login" className="text-accent hover:text-accent-hover transition-colors">
            {tc("backToLogin")}
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordForm />
    </Suspense>
  );
}
