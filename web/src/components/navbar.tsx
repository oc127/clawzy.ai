"use client";

import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { useLanguage } from "@/context/language-context";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/logo";
import { LanguageSwitcher } from "@/components/language-switcher";

export function Navbar() {
  const { user, logout } = useAuth();
  const { t } = useLanguage();

  return (
    <nav className="sticky top-0 z-50 border-b border-[#ebebeb] bg-white/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center">
          <Logo size="sm" />
        </Link>

        <div className="flex items-center gap-2">
          <LanguageSwitcher />

          {user ? (
            <>
              <Link href="/dashboard">
                <Button variant="ghost" size="sm" className="text-[#222222] hover:bg-[#f7f7f7]">
                  {t.nav.dashboard}
                </Button>
              </Link>
              <span className="hidden text-sm text-[#717171] md:inline">
                {user.name}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={logout}
                className="border-[#dddddd] text-[#222222] hover:border-[#b0b0b0]"
              >
                {t.nav.logout}
              </Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button variant="ghost" size="sm" className="text-[#222222] hover:bg-[#f7f7f7]">
                  {t.nav.login}
                </Button>
              </Link>
              <Link href="/register">
                <Button
                  size="sm"
                  className="bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl px-5 font-semibold shadow-sm"
                >
                  {t.nav.signup}
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
