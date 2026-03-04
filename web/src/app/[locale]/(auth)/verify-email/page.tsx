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
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-md space-y-6 text-center">
        <h1 className="text-4xl font-bold text-white">🦞</h1>

        {status === "loading" && (
          <>
            <h2 className="text-2xl font-bold text-white">{t("verifying")}</h2>
            <p className="text-gray-400">{t("verifyingDesc")}</p>
          </>
        )}

        {status === "success" && (
          <>
            <h2 className="text-2xl font-bold text-green-400">{t("verifySuccessTitle")}</h2>
            <p className="text-gray-400">{message}</p>
            <Link
              href="/"
              className="inline-block mt-4 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition"
            >
              {t("goToDashboard")}
            </Link>
          </>
        )}

        {status === "error" && (
          <>
            <h2 className="text-2xl font-bold text-red-400">{t("verifyFailTitle")}</h2>
            <p className="text-gray-400">{message}</p>
            <Link href="/login" className="inline-block text-blue-400 hover:underline text-sm mt-4">
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
