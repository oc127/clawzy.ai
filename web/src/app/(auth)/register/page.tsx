"use client";

import { useState, useEffect, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { ApiError, apiGet } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Logo } from "@/components/logo";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface OAuthProvider {
  id: string;
  name: string;
}

function GitHubIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

function GoogleIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  );
}

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [providers, setProviders] = useState<OAuthProvider[]>([]);
  const [oauthLoading, setOauthLoading] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/v1/auth/providers")
      .then((r) => r.json())
      .then((data) => setProviders(data.providers || []))
      .catch(() => {});
  }, []);

  const validate = (field: string, value?: string) => {
    const errs = { ...fieldErrors };
    if (field === "email") {
      const v = value ?? email;
      if (v && !EMAIL_RE.test(v)) errs.email = "Invalid email format";
      else delete errs.email;
    }
    if (field === "password") {
      const v = value ?? password;
      if (v && v.length < 8) errs.password = "At least 8 characters";
      else delete errs.password;
      if (confirmPassword && v !== confirmPassword)
        errs.confirmPassword = "Passwords do not match";
      else delete errs.confirmPassword;
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

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setSubmitting(true);
    try {
      await register(email, password, name);
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

  async function handleOAuth(providerId: string) {
    setOauthLoading(providerId);
    try {
      const data = await apiGet<{ url: string; state: string }>(
        `/auth/${providerId}/authorize`
      );
      window.location.href = data.url;
    } catch {
      setError(`Failed to connect to ${providerId}`);
      setOauthLoading(null);
    }
  }

  const inputClass = (field: string) =>
    fieldErrors[field]
      ? "border-destructive focus:ring-destructive"
      : "";

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center text-center">
          <Logo size="lg" className="mb-4" />
          <h1 className="text-2xl font-bold">Create your account</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Get started with 500 free credits
          </p>
        </div>

        {/* OAuth Buttons */}
        {providers.length > 0 && (
          <>
            <div className="space-y-3 mb-6">
              {providers.map((p) => (
                <Button
                  key={p.id}
                  variant="outline"
                  className="w-full gap-3"
                  onClick={() => handleOAuth(p.id)}
                  loading={oauthLoading === p.id}
                  disabled={oauthLoading !== null}
                >
                  {p.id === "github" && <GitHubIcon />}
                  {p.id === "google" && <GoogleIcon />}
                  Continue with {p.name}
                </Button>
              ))}
            </div>
            <div className="relative mb-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-card px-2 text-muted-foreground">or</span>
              </div>
            </div>
          </>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-400" role="alert">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="reg-name" className="mb-1.5 block text-sm font-medium">Name</label>
            <Input
              id="reg-name"
              type="text"
              placeholder="Your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div>
            <label htmlFor="reg-email" className="mb-1.5 block text-sm font-medium">Email</label>
            <Input
              id="reg-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onBlur={() => validate("email")}
              className={inputClass("email")}
              aria-describedby={fieldErrors.email ? "email-error" : undefined}
              required
            />
            {fieldErrors.email && (
              <p id="email-error" className="mt-1 text-xs text-destructive">{fieldErrors.email}</p>
            )}
          </div>

          <div>
            <label htmlFor="reg-password" className="mb-1.5 block text-sm font-medium">
              Password
            </label>
            <Input
              id="reg-password"
              type="password"
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                validate("password", e.target.value);
              }}
              className={inputClass("password")}
              aria-describedby={fieldErrors.password ? "password-error" : undefined}
              required
              minLength={8}
            />
            {fieldErrors.password && (
              <p id="password-error" className="mt-1 text-xs text-destructive">{fieldErrors.password}</p>
            )}
          </div>

          <div>
            <label htmlFor="reg-confirm" className="mb-1.5 block text-sm font-medium">
              Confirm Password
            </label>
            <Input
              id="reg-confirm"
              type="password"
              placeholder="Repeat your password"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                validate("confirmPassword", e.target.value);
              }}
              className={inputClass("confirmPassword")}
              aria-describedby={fieldErrors.confirmPassword ? "confirm-error" : undefined}
              required
            />
            {fieldErrors.confirmPassword && (
              <p id="confirm-error" className="mt-1 text-xs text-destructive">{fieldErrors.confirmPassword}</p>
            )}
          </div>

          <Button type="submit" className="w-full" loading={submitting}>
            Create Account
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}
