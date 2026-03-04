"use client";

import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { updateMe, changePassword } from "@/lib/api";

export default function SettingsPage() {
  const { user, logout, refetch } = useAuth();

  // Edit name
  const [name, setName] = useState("");
  const [nameLoading, setNameLoading] = useState(false);
  const [nameMsg, setNameMsg] = useState("");

  // Change password
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [pwLoading, setPwLoading] = useState(false);
  const [pwMsg, setPwMsg] = useState("");
  const [pwError, setPwError] = useState("");

  async function handleNameSave(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setNameLoading(true);
    setNameMsg("");
    try {
      await updateMe({ name: name.trim() });
      setNameMsg("已更新");
      setName("");
      refetch();
    } catch (err: unknown) {
      setNameMsg(err instanceof Error ? err.message : "更新失败");
    } finally {
      setNameLoading(false);
    }
  }

  async function handlePasswordChange(e: React.FormEvent) {
    e.preventDefault();
    setPwError("");
    setPwMsg("");

    if (newPw.length < 6) {
      setPwError("新密码至少 6 个字符");
      return;
    }
    if (newPw !== confirmPw) {
      setPwError("两次密码不一致");
      return;
    }

    setPwLoading(true);
    try {
      await changePassword(currentPw, newPw);
      setPwMsg("密码已更新");
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
    } catch (err: unknown) {
      setPwError(err instanceof Error ? err.message : "修改失败");
    } finally {
      setPwLoading(false);
    }
  }

  const inputClass =
    "w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500";

  return (
    <div className="p-8 max-w-2xl space-y-8">
      <h1 className="text-2xl font-bold text-white">设置</h1>

      {/* Profile */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-semibold text-white">个人资料</h2>
        <div>
          <label className="text-sm text-gray-500">邮箱</label>
          <p className="text-white">{user?.email}</p>
        </div>
        <form onSubmit={handleNameSave} className="space-y-3">
          <div>
            <label className="text-sm text-gray-500">名字</label>
            <input
              type="text"
              placeholder={user?.name || ""}
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={inputClass}
            />
          </div>
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={nameLoading || !name.trim()}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white text-sm font-semibold rounded-lg transition"
            >
              {nameLoading ? "保存中..." : "保存"}
            </button>
            {nameMsg && <span className="text-sm text-green-400">{nameMsg}</span>}
          </div>
        </form>
      </div>

      {/* Change Password */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-semibold text-white">修改密码</h2>
        <form onSubmit={handlePasswordChange} className="space-y-3">
          {pwError && (
            <div className="bg-red-900/30 border border-red-700 text-red-300 rounded-lg p-3 text-sm">
              {pwError}
            </div>
          )}
          {pwMsg && (
            <div className="bg-green-900/30 border border-green-700 text-green-300 rounded-lg p-3 text-sm">
              {pwMsg}
            </div>
          )}
          <input
            type="password"
            placeholder="当前密码"
            value={currentPw}
            onChange={(e) => setCurrentPw(e.target.value)}
            required
            className={inputClass}
          />
          <input
            type="password"
            placeholder="新密码"
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            required
            minLength={6}
            className={inputClass}
          />
          <input
            type="password"
            placeholder="确认新密码"
            value={confirmPw}
            onChange={(e) => setConfirmPw(e.target.value)}
            required
            minLength={6}
            className={inputClass}
          />
          <button
            type="submit"
            disabled={pwLoading}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white text-sm font-semibold rounded-lg transition"
          >
            {pwLoading ? "修改中..." : "修改密码"}
          </button>
        </form>
      </div>

      {/* Logout */}
      <button
        onClick={logout}
        className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition"
      >
        退出登录
      </button>
    </div>
  );
}
