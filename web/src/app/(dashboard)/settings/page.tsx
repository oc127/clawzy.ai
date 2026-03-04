"use client";

import { useAuth } from "@/hooks/useAuth";

export default function SettingsPage() {
  const { user, logout } = useAuth();

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-8">设置</h1>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <div>
          <label className="text-sm text-gray-500">名字</label>
          <p className="text-white">{user?.name}</p>
        </div>
        <div>
          <label className="text-sm text-gray-500">邮箱</label>
          <p className="text-white">{user?.email}</p>
        </div>
      </div>

      <button
        onClick={logout}
        className="mt-8 px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition"
      >
        退出登录
      </button>
    </div>
  );
}
