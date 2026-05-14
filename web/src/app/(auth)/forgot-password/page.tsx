"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useLanguage } from "@/context/language-context";
import { apiPost } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export default function ForgotPasswordPage() {
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await apiPost("/auth/forgot-password", { email });
      setSent(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen bg-white items-center justify-center px-6 py-16">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mb-3 text-4xl">🦞</div>
          <h1 className="text-2xl font-extrabold text-[#222222]">{t.auth.forgotPassword.title}</h1>
          <p className="mt-1 text-sm text-[#717171]">{t.auth.forgotPassword.subtitle}</p>
        </div>

        {sent ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 rounded-xl bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-700">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              {t.auth.forgotPassword.sent}
            </div>
            <div className="text-center">
              <Link href="/login" className="text-sm font-semibold text-[#ff385c] hover:underline">
                {t.auth.forgotPassword.backToLogin}
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="flex items-center gap-2 rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600" role="alert">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222]">{t.auth.forgotPassword.email}</label>
              <Input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full h-12 rounded-xl bg-[#ff385c] hover:bg-[#e31c5f] text-white font-bold text-base shadow-[0_4px_14px_rgba(255,56,92,0.30)] hover:shadow-[0_6px_20px_rgba(255,56,92,0.40)] transition-all"
              loading={submitting}
            >
              {t.auth.forgotPassword.submit}
            </Button>

            <div className="text-center">
              <Link href="/login" className="text-sm font-semibold text-[#ff385c] hover:underline">
                {t.auth.forgotPassword.backToLogin}
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
