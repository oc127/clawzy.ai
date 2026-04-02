'use client'

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { User } from './types'
import { getMe, login as apiLogin, register as apiRegister, clearTokens } from './api'

interface AuthState {
  user: User | null
  loading: boolean
  error: string | null
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
  })

  const refreshUser = useCallback(async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
      if (!token) {
        setState({ user: null, loading: false, error: null })
        return
      }
      const user = await getMe()
      setState({ user, loading: false, error: null })
    } catch {
      setState({ user: null, loading: false, error: null })
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const login = async (email: string, password: string) => {
    setState(s => ({ ...s, loading: true, error: null }))
    try {
      await apiLogin(email, password)
      const user = await getMe()
      setState({ user, loading: false, error: null })
    } catch (err) {
      setState(s => ({ ...s, loading: false, error: (err as Error).message }))
      throw err
    }
  }

  const register = async (email: string, password: string, name: string) => {
    setState(s => ({ ...s, loading: true, error: null }))
    try {
      await apiRegister(email, password, name)
      const user = await getMe()
      setState({ user, loading: false, error: null })
    } catch (err) {
      setState(s => ({ ...s, loading: false, error: (err as Error).message }))
      throw err
    }
  }

  const logout = () => {
    clearTokens()
    setState({ user: null, loading: false, error: null })
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
