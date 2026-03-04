"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
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
  const pathname = usePathname();
  const t = useTranslations("dashboard");
  const tc = useTranslations("common");

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-muted text-sm">{t("lobsterWaking")}</p>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className="w-56 border-r border-border flex flex-col">
        <div className="px-5 py-6">
          <Link href="/" className="text-base font-semibold text-foreground tracking-tight">
            Clawzy
          </Link>
        </div>

        <nav className="flex-1 px-3 space-y-0.5">
          <NavLink href="/" label={t("myLobsters")} active={pathname === "/"} />
          <NavLink href="/agents" label={t("manageLobsters")} active={pathname === "/agents"} />
          <NavLink href="/billing" label={t("energyAndPlans")} active={pathname === "/billing"} />
          <NavLink href="/settings" label={tc("settings")} active={pathname === "/settings"} />
        </nav>

        <div className="px-4 py-4 border-t border-border space-y-3">
          <LanguageSwitcher className="w-full" />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-foreground">{user.name}</p>
              <p className="text-xs text-muted">{t("energyAvailable", { balance: user.credit_balance })}</p>
            </div>
            <button
              onClick={logout}
              className="text-xs text-muted hover:text-foreground transition-colors"
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

function NavLink({ href, label, active }: { href: string; label: string; active?: boolean }) {
  return (
    <Link
      href={href}
      className={`block px-3 py-2 rounded-md text-sm transition-colors ${
        active
          ? "text-foreground bg-surface"
          : "text-muted hover:text-foreground hover:bg-surface"
      }`}
    >
      {label}
    </Link>
  );
}
