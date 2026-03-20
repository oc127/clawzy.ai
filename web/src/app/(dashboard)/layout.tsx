"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";
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
} from "lucide-react";

const sidebarLinks = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, gradient: "icon-gradient-red" },
  { href: "/agents", label: "Agents", icon: Bot, gradient: "icon-gradient-blue" },
  { href: "/clawhub", label: "ClawHub", icon: Package, gradient: "icon-gradient-purple" },
  { href: "/models", label: "Models", icon: Cpu, gradient: "icon-gradient-teal" },
  { href: "/billing", label: "Billing", icon: CreditCard, gradient: "icon-gradient-green" },
  { href: "/settings", label: "Settings", icon: Settings, gradient: "icon-gradient-orange" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [user, loading, router]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white">
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
    <div className="flex min-h-screen bg-[#f7f7f7]">
      {/* Mobile top bar */}
      <div className="fixed inset-x-0 top-0 z-20 flex h-14 items-center border-b border-[#ebebeb] bg-white px-4 md:hidden">
        <button
          onClick={() => setSidebarOpen(true)}
          className="rounded-lg p-1.5 text-[#717171] hover:bg-[#f7f7f7] transition-colors"
          aria-label="Open sidebar"
        >
          <Menu className="h-5 w-5" />
        </button>
        <span className="ml-3 text-base font-bold text-[#222222]">NipponClaw</span>
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
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-[#ebebeb] bg-white transition-transform duration-200 ease-out",
          "md:relative md:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Brand */}
        <div className="flex h-16 items-center justify-between border-b border-[#ebebeb] px-5">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl">🦞</span>
            <span className="text-base font-extrabold text-[#222222]">NipponClaw</span>
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
                    ? "bg-[#fff0f2] text-[#ff385c]"
                    : "text-[#717171] hover:bg-[#f7f7f7] hover:text-[#222222]"
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
        <div className="border-t border-[#ebebeb] p-4">
          <div className="mb-3 flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#ff385c] to-[#ff8c69] text-white text-sm font-bold shadow-sm">
              {initials}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-[#222222]">{user.name}</p>
              <p className="truncate text-xs text-[#717171]">{user.email}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 text-[#717171] hover:bg-[#f7f7f7] hover:text-[#222222] rounded-xl"
            onClick={() => { logout(); router.push("/"); }}
          >
            <LogOut className="h-4 w-4" />
            Log out
          </Button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-x-hidden pt-14 md:pt-0">
        <div key={pathname} className="animate-page-enter min-h-full p-5 md:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
