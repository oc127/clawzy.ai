"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { useLanguage } from "@/context/language-context";
import { ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AlertCircle, CheckCircle2 } from "lucide-react";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const { t } = useLanguage();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const validate = (field: string, value?: string) => {
    const errs = { ...fieldErrors };
    if (field === "email") {
      const v = value ?? email;
      if (v && !EMAIL_RE.test(v)) errs.email = "Invalid email format";
      else delete errs.email;
    }
    if (field === "password") {
      const v = value ?? password;
      if (v && v.length < 6) errs.password = "At least 6 characters";
      else delete errs.password;
      if (confirmPassword && v !== confirmPassword)
        errs.confirmPassword = "Passwords do not match";
      else if (confirmPassword) delete errs.confirmPassword;
    }
    if (field === "confirmPassword") {
      const v = value ?? confirmPassword;
      if (v && v !== password) errs.confirmPassword = "Passwords do not match";
      else delete errs.confirmPassword;
    }
    setFieldErrors(errs);
  };

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (password !== confirmPassword) { setError("Passwords do not match."); return; }
    if (password.length < 6) { setError("Password must be at least 6 characters."); return; }
    setSubmitting(true);
    try {
      await register(email, password, name);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) setError(err.detail);
      else setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass = (field: string) =>
    fieldErrors[field]
      ? "border-red-400 focus-visible:border-red-400 focus-visible:ring-red-200"
      : "";

  const perks = [
    t.auth.register.perk1,
    t.auth.register.perk2,
    t.auth.register.perk3,
  ];

  return (
    <div className="flex min-h-screen bg-white">
      {/* Left decorative panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#ff385c] to-[#ff8c69] flex-col items-center justify-center p-12 text-white">
        <div className="max-w-sm">
          <div className="mb-8 text-6xl">🦞</div>
          <h2 className="text-3xl font-extrabold mb-4">{t.auth.register.leftTitle}</h2>
          <p className="text-white/80 text-lg leading-relaxed mb-8">
            {t.auth.register.subtitle}
          </p>
          <ul className="space-y-3">
            {perks.map((perk) => (
              <li key={perk} className="flex items-center gap-3 text-sm">
                <CheckCircle2 className="h-5 w-5 text-white shrink-0" />
                <span>{perk}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex w-full lg:w-1/2 flex-col items-center justify-center px-6 py-16">
        <div className="w-full max-w-sm">
          <div className="mb-8 text-center">
            <div className="mb-3 text-4xl">🦞</div>
            <h1 className="text-2xl font-extrabold text-[#222222]">{t.auth.register.title}</h1>
            <p className="mt-1 text-sm text-[#717171]">{t.auth.register.subtitle}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="flex items-center gap-2 rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600" role="alert">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222]">{t.auth.register.name}</label>
              <Input
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222]">{t.auth.register.email}</label>
              <Input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={() => validate("email")}
                className={inputClass("email")}
                required
              />
              {fieldErrors.email && (
                <p className="text-xs text-red-500">{fieldErrors.email}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222]">{t.auth.register.password}</label>
              <Input
                type="password"
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => { setPassword(e.target.value); validate("password", e.target.value); }}
                className={inputClass("password")}
                required
                minLength={6}
              />
              {fieldErrors.password && (
                <p className="text-xs text-red-500">{fieldErrors.password}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222]">Confirm password</label>
              <Input
                type="password"
                placeholder="Repeat your password"
                value={confirmPassword}
                onChange={(e) => { setConfirmPassword(e.target.value); validate("confirmPassword", e.target.value); }}
                className={inputClass("confirmPassword")}
                required
              />
              {fieldErrors.confirmPassword && (
                <p className="text-xs text-red-500">{fieldErrors.confirmPassword}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full h-12 rounded-xl bg-[#ff385c] hover:bg-[#e31c5f] text-white font-bold text-base shadow-[0_4px_14px_rgba(255,56,92,0.30)] hover:shadow-[0_6px_20px_rgba(255,56,92,0.40)] transition-all"
              loading={submitting}
            >
              {t.auth.register.submit}
            </Button>

            <p className="text-xs text-center text-[#b0b0b0]">
              By signing up, you agree to our Terms of Service.
            </p>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-[#717171]">
              {t.auth.register.haveAccount}{" "}
              <Link href="/login" className="font-semibold text-[#ff385c] hover:underline">
                {t.auth.register.login}
              </Link>
            </p>
          </div>

          <div className="mt-6 text-center">
            <Link href="/" className="text-xs text-[#b0b0b0] hover:text-[#717171] transition-colors">
              ← Back to homepage
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
