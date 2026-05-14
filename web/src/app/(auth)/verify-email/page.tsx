"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { apiPost, ApiError } from "@/lib/api";
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setError("Missing verification token.");
      return;
    }
    apiPost("/auth/verify-email", { token })
      .then(() => setStatus("success"))
      .catch((err) => {
        setStatus("error");
        setError(err instanceof ApiError ? err.detail : "Verification failed. The link may have expired.");
      });
  }, [token]);

  return (
    <div className="flex min-h-screen bg-white dark:bg-[#111] items-center justify-center px-6 py-16">
      <div className="w-full max-w-sm text-center">
        <div className="mb-6 text-4xl">🦞</div>

        {status === "loading" && (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-[#ff385c]" />
            <p className="text-[#717171] dark:text-[#a0a0a0]">Verifying your email...</p>
          </div>
        )}

        {status === "success" && (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2 rounded-xl bg-green-50 dark:bg-emerald-900/20 border border-green-200 dark:border-emerald-800 px-4 py-3 text-sm text-green-700 dark:text-emerald-400">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              Email verified successfully!
            </div>
            <Link href="/dashboard" className="text-sm font-semibold text-[#ff385c] hover:underline">
              Go to Dashboard
            </Link>
          </div>
        )}

        {status === "error" && (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-600 dark:text-red-400">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
            <Link href="/login" className="text-sm font-semibold text-[#ff385c] hover:underline">
              Back to Login
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
