"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { useLanguage } from "@/context/language-context";
import { useTheme } from "@/context/theme-context";
import { apiPost } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import { Logo } from "@/components/logo";
import { LanguageSwitcher } from "@/components/language-switcher";
import { toast } from "sonner";
import {
  LayoutDashboard,
  Bot,
  Cpu,
  CreditCard,
  Settings,
  LogOut,
  Menu,
  X,
  Package,
  Sun,
  Moon,
  Mail,
  Brain,
} from "lucide-react";

const SIDEBAR_LINKS_CONFIG = [
  { href: "/dashboard", key: "dashboard" as const, icon: LayoutDashboard, gradient: "icon-gradient-red" },
  { href: "/agents", key: "agents" as const, icon: Bot, gradient: "icon-gradient-blue" },
  { href: "/clawhub", key: "clawhub" as const, icon: Package, gradient: "icon-gradient-purple" },
  { href: "/models", key: "models" as const, icon: Cpu, gradient: "icon-gradient-teal" },
  { href: "/memory", key: "memory" as const, icon: Brain, gradient: "icon-gradient-pink" },
  { href: "/billing", key: "billing" as const, icon: CreditCard, gradient: "icon-gradient-green" },
  { href: "/settings", key: "settings" as const, icon: Settings, gradient: "icon-gradient-orange" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading, logout } = useAuth();
  const { t } = useLanguage();
  const { resolved, setTheme } = useTheme();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sendingVerification, setSendingVerification] = useState(false);

  const handleResendVerification = useCallback(async () => {
    setSendingVerification(true);
    try {
      await apiPost("/auth/send-verification");
      toast.success("Verification email sent!");
    } catch {
      toast.error("Failed to send verification email");
    } finally {
      setSendingVerification(false);
    }
  }, []);

  const DASHBOARD_KEY_MAP: Record<string, string> = {
    dashboard: t.dashboard.title,
    agents: t.dashboard.agents,
    clawhub: t.dashboard.clawhub,
    memory: t.dashboard.memory,
    models: t.dashboard.models,
    billing: t.dashboard.billing,
    settings: t.dashboard.settings,
  };

  const sidebarLinks = SIDEBAR_LINKS_CONFIG.map((link) => ({
    ...link,
    label: DASHBOARD_KEY_MAP[link.key] ?? link.key,
  }));

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [user, loading, router]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white dark:bg-[#111]">
        <div className="flex items-center gap-3">
          <svg className="h-5 w-5 animate-spin text-[#ff385c]" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-[#717171] text-sm">Loading...</span>
        </div>
      </div>
    );
  }

  if (!user) return null;

  const initials = user.name
    ? user.name.split(" ").map((n: string) => n[0]).join("").toUpperCase().slice(0, 2)
    : user.email[0].toUpperCase();

  return (
    <div className="flex min-h-screen bg-[#f7f7f7] dark:bg-[#111]">
      {/* Mobile top bar */}
      <div className="fixed inset-x-0 top-0 z-20 flex h-14 items-center border-b border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] px-4 md:hidden">
        <button
          onClick={() => setSidebarOpen(true)}
          className="rounded-lg p-1.5 text-[#717171] hover:bg-[#f7f7f7] transition-colors"
          aria-label="Open sidebar"
        >
          <Menu className="h-5 w-5" />
        </button>
        <span className="ml-3 text-base font-extrabold text-[#222222] dark:text-white">
          <span className="text-[#ff385c]">Nippon</span>Claw
        </span>
      </div>

      {/* Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/30 backdrop-blur-sm md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] transition-transform duration-200 ease-out",
          "md:relative md:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Brand */}
        <div className="flex h-16 items-center justify-between border-b border-[#ebebeb] dark:border-[#333] px-5">
          <Link href="/" className="flex items-center">
            <Logo size="sm" />
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-md p-1 text-[#717171] hover:bg-[#f7f7f7] md:hidden transition-colors"
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 space-y-0.5 px-3 py-4">
          {sidebarLinks.map((link) => {
            const isActive =
              pathname === link.href ||
              (link.href !== "/dashboard" && pathname.startsWith(link.href + "/"));
            return (
              <Link
                key={link.label}
                href={link.href}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                  isActive
                    ? "bg-[#fff0f2] dark:bg-[#ff385c]/10 text-[#ff385c]"
                    : "text-[#717171] hover:bg-[#f7f7f7] dark:hover:bg-[#262626] hover:text-[#222222] dark:hover:text-white"
                )}
              >
                <div
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-lg",
                    isActive ? link.gradient + " shadow-sm" : "bg-[#f7f7f7]"
                  )}
                >
                  <link.icon className={cn("h-3.5 w-3.5", isActive ? "text-white" : "text-[#717171]")} />
                </div>
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* User footer */}
        <div className="border-t border-[#ebebeb] dark:border-[#333] p-4">
          <div className="mb-3 flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#ff385c] to-[#ff8c69] text-white text-sm font-bold shadow-sm">
              {initials}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-[#222222] dark:text-white">{user.name}</p>
              <p className="truncate text-xs text-[#717171] dark:text-[#a0a0a0]">{user.email}</p>
            </div>
          </div>
          <div className="mb-2 flex items-center gap-2">
            <LanguageSwitcher compact />
            <button
              onClick={() => setTheme(resolved === "dark" ? "light" : "dark")}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-[#717171] hover:bg-[#f7f7f7] dark:hover:bg-[#262626] transition-colors"
              aria-label="Toggle dark mode"
            >
              {resolved === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 text-[#717171] hover:bg-[#f7f7f7] hover:text-[#222222] rounded-xl"
            onClick={() => { logout(); router.push("/"); }}
          >
            <LogOut className="h-4 w-4" />
            {t.nav.logout}
          </Button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-x-hidden pt-14 md:pt-0">
        {!user.email_verified && (
          <div className="mx-5 mt-5 md:mx-8 md:mt-8 mb-0 flex items-center gap-3 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 px-4 py-3 text-sm text-amber-700 dark:text-amber-400">
            <Mail className="h-4 w-4 shrink-0" />
            <span className="flex-1">Please verify your email address to secure your account.</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleResendVerification}
              disabled={sendingVerification}
              className="shrink-0 text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/30 rounded-lg font-semibold"
            >
              {sendingVerification ? "Sending..." : "Resend"}
            </Button>
          </div>
        )}
        <div key={pathname} className="animate-page-enter min-h-full p-5 md:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
