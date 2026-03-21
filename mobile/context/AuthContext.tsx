import React, { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { router } from "expo-router";
import { loginApi, registerApi, getMe, type User } from "@/lib/api";
import { saveTokens, clearTokens, getAccessToken } from "@/lib/storage";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const token = await getAccessToken();
      if (token) {
        try {
          const me = await getMe();
          setUser(me);
        } catch {
          await clearTokens();
        }
      }
      setLoading(false);
    })();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await loginApi(email, password);
    await saveTokens(res.access_token, res.refresh_token);
    const me = await getMe();
    setUser(me);
    router.replace("/(tabs)");
  };

  const register = async (email: string, password: string, name: string) => {
    const res = await registerApi(email, password, name);
    await saveTokens(res.access_token, res.refresh_token);
    const me = await getMe();
    setUser(me);
    router.replace("/(tabs)");
  };

  const logout = async () => {
    await clearTokens();
    setUser(null);
    router.replace("/(auth)/login");
  };

  const refreshUser = async () => {
    const me = await getMe();
    setUser(me);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
