"use client";

import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/logo";

export function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="sticky top-0 z-50 border-b border-[#ebebeb] bg-white/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center">
          <Logo size="md" />
        </Link>

        <div className="flex items-center gap-2">
          {user ? (
            <>
              <Link href="/dashboard">
                <Button variant="ghost" size="sm" className="text-[#222222] hover:bg-[#f7f7f7]">
                  Dashboard
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
                Logout
              </Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button variant="ghost" size="sm" className="text-[#222222] hover:bg-[#f7f7f7]">
                  Log in
                </Button>
              </Link>
              <Link href="/register">
                <Button
                  size="sm"
                  className="bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl px-5 font-semibold shadow-sm"
                >
                  Sign up
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
