"use client";

import { useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useLanguage } from "@/context/language-context";
import { apiPost, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export default function ResetPasswordPage() {
  const { t } = useLanguage();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setError(t.auth.resetPassword.mismatch);
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await apiPost("/auth/reset-password", { token, new_password: password });
      setSuccess(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen bg-white items-center justify-center px-6 py-16">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mb-3 text-4xl">🦞</div>
          <h1 className="text-2xl font-extrabold text-[#222222]">{t.auth.resetPassword.title}</h1>
          <p className="mt-1 text-sm text-[#717171]">{t.auth.resetPassword.subtitle}</p>
        </div>

        {success ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 rounded-xl bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-700">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              {t.auth.resetPassword.success}
            </div>
            <div className="text-center">
              <Link href="/login" className="text-sm font-semibold text-[#ff385c] hover:underline">
                {t.auth.resetPassword.backToLogin}
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
              <label className="block text-sm font-semibold text-[#222222]">{t.auth.resetPassword.password}</label>
              <Input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222]">{t.auth.resetPassword.confirm}</label>
              <Input
                type="password"
                placeholder="••••••••"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                minLength={8}
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full h-12 rounded-xl bg-[#ff385c] hover:bg-[#e31c5f] text-white font-bold text-base shadow-[0_4px_14px_rgba(255,56,92,0.30)] hover:shadow-[0_6px_20px_rgba(255,56,92,0.40)] transition-all"
              loading={submitting}
              disabled={!token}
            >
              {t.auth.resetPassword.submit}
            </Button>

            <div className="text-center">
              <Link href="/login" className="text-sm font-semibold text-[#ff385c] hover:underline">
                {t.auth.resetPassword.backToLogin}
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
