'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export default function LandingPage() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && user) {
      router.replace('/dashboard')
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (user) return null

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      {/* Hero */}
      <div className="text-center max-w-2xl mx-auto">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <div className="w-20 h-20 rounded-2xl bg-brand flex items-center justify-center">
            <span className="text-4xl font-bold text-white">C</span>
          </div>
        </div>

        <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4 tracking-tight">
          Clawzy<span className="text-brand">.ai</span>
        </h1>
        <p className="text-xl text-neutral-400 mb-2">NipponClaw</p>
        <p className="text-neutral-500 mb-10 max-w-md mx-auto">
          AI Agentを作成して、あなただけのアシスタントと会話しましょう。
        </p>

        {/* CTA */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/login">
            <Button size="lg" className="w-full sm:w-auto min-w-[160px]">
              ログイン
            </Button>
          </Link>
          <Link href="/register">
            <Button variant="outline" size="lg" className="w-full sm:w-auto min-w-[160px]">
              新規登録
            </Button>
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="absolute bottom-6 text-center">
        <p className="text-xs text-neutral-600">&copy; 2024 NipponClaw. All rights reserved.</p>
      </footer>
    </div>
  )
}
