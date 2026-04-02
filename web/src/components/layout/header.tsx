'use client'

import { useAuth } from '@/lib/auth'
import { Button } from '@/components/ui/button'

export function Header() {
  const { user, logout } = useAuth()

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-neutral-800 bg-surface-200/80 backdrop-blur-sm px-6">
      {/* Mobile logo */}
      <div className="flex items-center gap-2 md:hidden">
        <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center text-white font-bold text-sm">
          C
        </div>
        <span className="text-lg font-bold text-neutral-100">Clawzy</span>
      </div>

      {/* Spacer for desktop (sidebar provides logo) */}
      <div className="hidden md:block" />

      {/* Right side */}
      <div className="flex items-center gap-4">
        {user && (
          <>
            <div className="hidden sm:flex items-center gap-2">
              <span className="text-sm text-neutral-400">{user.name || user.email}</span>
              <span className="text-xs text-brand font-medium">
                {user.credit_balance.toLocaleString()} credits
              </span>
            </div>
            <Button variant="ghost" size="sm" onClick={logout}>
              Logout
            </Button>
          </>
        )}
      </div>
    </header>
  )
}
