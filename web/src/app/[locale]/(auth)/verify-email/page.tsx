"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { verifyEmail } from "@/lib/api";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const t = useTranslations("auth");
  const tc = useTranslations("common");

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage(t("verifyInvalidLink"));
      return;
    }

    verifyEmail(token)
      .then(() => {
        setStatus("success");
        setMessage(t("verifySuccess"));
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : t("verifyFailed"));
      });
  }, [token, t]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-6 text-center">
        <h1 className="text-base font-semibold text-foreground tracking-tight">Clawzy</h1>

        {status === "loading" && (
          <>
            <h2 className="text-xl font-semibold text-foreground">{t("verifying")}</h2>
            <p className="text-sm text-muted">{t("verifyingDesc")}</p>
          </>
        )}

        {status === "success" && (
          <>
            <h2 className="text-xl font-semibold text-green-400">{t("verifySuccessTitle")}</h2>
            <p className="text-sm text-muted">{message}</p>
            <Link
              href="/"
              className="inline-block px-5 py-2.5 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-lg transition-colors"
            >
              {t("goToDashboard")}
            </Link>
          </>
        )}

        {status === "error" && (
          <>
            <h2 className="text-xl font-semibold text-red-400">{t("verifyFailTitle")}</h2>
            <p className="text-sm text-muted">{message}</p>
            <Link href="/login" className="inline-block text-sm text-accent hover:text-accent-hover transition-colors">
              {tc("backToLogin")}
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyEmailContent />
    </Suspense>
  );
}
