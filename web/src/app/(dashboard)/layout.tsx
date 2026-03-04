"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-gray-400 text-lg">🦞 龙虾正在醒来...</div>
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
          <NavLink href="/" label="我的龙虾" />
          <NavLink href="/agents" label="管理龙虾" />
          <NavLink href="/billing" label="能量 & 套餐" />
          <NavLink href="/settings" label="设置" />
        </nav>

        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white">{user.name}</p>
              <p className="text-xs text-gray-500">⚡ {user.credit_balance} 能量</p>
            </div>
            <button
              onClick={logout}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              退出
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
