"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { verifyEmail } from "@/lib/api";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("验证链接无效");
      return;
    }

    verifyEmail(token)
      .then(() => {
        setStatus("success");
        setMessage("邮箱验证成功！");
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "验证失败，链接可能已过期");
      });
  }, [token]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-md space-y-6 text-center">
        <h1 className="text-4xl font-bold text-white">🦞</h1>

        {status === "loading" && (
          <>
            <h2 className="text-2xl font-bold text-white">验证中...</h2>
            <p className="text-gray-400">正在验证你的邮箱，请稍候</p>
          </>
        )}

        {status === "success" && (
          <>
            <h2 className="text-2xl font-bold text-green-400">验证成功</h2>
            <p className="text-gray-400">{message}</p>
            <Link
              href="/"
              className="inline-block mt-4 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition"
            >
              进入控制台
            </Link>
          </>
        )}

        {status === "error" && (
          <>
            <h2 className="text-2xl font-bold text-red-400">验证失败</h2>
            <p className="text-gray-400">{message}</p>
            <Link href="/login" className="inline-block text-blue-400 hover:underline text-sm mt-4">
              返回登录
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
