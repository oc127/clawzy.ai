"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { forgotPassword } from "@/lib/api";

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
      <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
        <div className="w-full max-w-md space-y-6 text-center">
          <h1 className="text-4xl font-bold text-white">🦞</h1>
          <h2 className="text-2xl font-bold text-white">{t("emailSent")}</h2>
          <p className="text-gray-400">{t("emailSentDesc")}</p>
          <Link href="/login" className="inline-block text-blue-400 hover:underline text-sm">
            {tc("backToLogin")}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-white">🦞</h1>
          <h2 className="mt-4 text-2xl font-bold text-white">{t("forgotPasswordTitle")}</h2>
          <p className="mt-2 text-gray-400">{t("forgotPasswordDesc")}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-900/30 border border-red-700 text-red-300 rounded-lg p-3 text-sm">
              {error}
            </div>
          )}

          <input
            type="email"
            placeholder={t("email")}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-lg transition"
          >
            {loading ? t("sending") : t("sendResetLink")}
          </button>
        </form>

        <p className="text-center text-gray-500 text-sm">
          {t("remembered")}{" "}
          <Link href="/login" className="text-blue-400 hover:underline">
            {tc("backToLogin")}
          </Link>
        </p>
      </div>
    </div>
  );
}
