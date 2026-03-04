"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useAuth } from "@/hooks/useAuth";
import LanguageSwitcher from "@/components/LanguageSwitcher";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const t = useTranslations("dashboard");
  const tc = useTranslations("common");

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-gray-400 text-lg">{t("lobsterWaking")}</div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-950 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-6">
          <Link href="/" className="text-xl font-bold text-white flex items-center gap-2">
            🦞 Clawzy
          </Link>
        </div>

        <nav className="flex-1 px-4 space-y-1">
          <NavLink href="/" label={t("myLobsters")} />
          <NavLink href="/agents" label={t("manageLobsters")} />
          <NavLink href="/billing" label={t("energyAndPlans")} />
          <NavLink href="/settings" label={tc("settings")} />
        </nav>

        <div className="px-4 py-3 border-t border-gray-800">
          <LanguageSwitcher className="w-full mb-3" />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white">{user.name}</p>
              <p className="text-xs text-gray-500">{t("energyAvailable", { balance: user.credit_balance })}</p>
            </div>
            <button
              onClick={logout}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              {tc("logout")}
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}

function NavLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="block px-4 py-2.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition text-sm"
    >
      {label}
    </Link>
  );
}
