"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Logo } from "@/components/logo";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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
      // also re-check confirmPassword
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

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
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

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-400" role="alert">
              {error}
            </div>
          )}

          <div>
            <label className="mb-1.5 block text-sm font-medium">Name</label>
            <Input
              type="text"
              placeholder="Your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium">Email</label>
            <Input
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
            <label className="mb-1.5 block text-sm font-medium">
              Password
            </label>
            <Input
              type="password"
              placeholder="At least 6 characters"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                validate("password", e.target.value);
              }}
              className={inputClass("password")}
              aria-describedby={fieldErrors.password ? "password-error" : undefined}
              required
              minLength={6}
            />
            {fieldErrors.password && (
              <p id="password-error" className="mt-1 text-xs text-destructive">{fieldErrors.password}</p>
            )}
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium">
              Confirm Password
            </label>
            <Input
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
