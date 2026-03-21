"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { useLanguage } from "@/context/language-context";
import { ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AlertCircle } from "lucide-react";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [emailError, setEmailError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      router.push("/dashboard");
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
    <div className="flex min-h-screen bg-white">
      {/* Left decorative panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#ff385c] to-[#ff8c69] flex-col items-center justify-center p-12 text-white">
        <div className="max-w-sm text-center">
          <div className="mb-8 text-6xl font-black">🦞</div>
          <h2 className="text-3xl font-extrabold mb-4">{t.auth.login.leftTitle}</h2>
          <p className="text-white/80 text-lg leading-relaxed">
            {t.auth.login.subtitle}
          </p>
          <div className="mt-8 grid grid-cols-3 gap-4 text-center">
            {[["500", t.auth.login.leftStat1], ["10+", t.auth.login.leftStat2], ["24/7", t.auth.login.leftStat3]].map(([val, label]) => (
              <div key={label} className="rounded-2xl bg-white/15 p-3">
                <p className="text-2xl font-black">{val}</p>
                <p className="text-xs text-white/70 mt-0.5">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex w-full lg:w-1/2 flex-col items-center justify-center px-6 py-16">
        <div className="w-full max-w-sm">
          {/* Logo / Brand */}
          <div className="mb-8 text-center">
            <div className="mb-3 text-4xl">🦞</div>
            <h1 className="text-2xl font-extrabold text-[#222222]">{t.auth.login.title}</h1>
            <p className="mt-1 text-sm text-[#717171]">{t.auth.login.subtitle}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="flex items-center gap-2 rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600" role="alert">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222]">{t.auth.login.email}</label>
              <Input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={() => {
                  if (email && !EMAIL_RE.test(email)) setEmailError("Invalid email format");
                  else setEmailError("");
                }}
                className={emailError ? "border-red-400 focus-visible:border-red-400 focus-visible:ring-red-200" : ""}
                aria-describedby={emailError ? "login-email-error" : undefined}
                required
              />
              {emailError && (
                <p id="login-email-error" className="text-xs text-red-500">{emailError}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="block text-sm font-semibold text-[#222222]">{t.auth.login.password}</label>
              </div>
              <Input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full h-12 rounded-xl bg-[#ff385c] hover:bg-[#e31c5f] text-white font-bold text-base shadow-[0_4px_14px_rgba(255,56,92,0.30)] hover:shadow-[0_6px_20px_rgba(255,56,92,0.40)] transition-all"
              loading={submitting}
            >
              {t.auth.login.submit}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-[#717171]">
              {t.auth.login.noAccount}{" "}
              <Link href="/register" className="font-semibold text-[#ff385c] hover:underline">
                {t.auth.login.signup}
              </Link>
            </p>
          </div>

          <div className="mt-8 text-center">
            <Link href="/" className="text-xs text-[#b0b0b0] hover:text-[#717171] transition-colors">
              ← Back to homepage
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
