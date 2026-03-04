"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@/hooks/useAuth";
import { updateMe, changePassword } from "@/lib/api";

const inputClass =
  "w-full px-4 py-2.5 bg-surface border border-border rounded-lg text-foreground placeholder-muted text-sm focus:outline-none focus:border-accent transition-colors";

export default function SettingsPage() {
  const { user, logout, refetch } = useAuth();
  const t = useTranslations("settings");
  const tc = useTranslations("common");

  const [name, setName] = useState("");
  const [nameLoading, setNameLoading] = useState(false);
  const [nameMsg, setNameMsg] = useState("");

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
      setNameMsg(t("updated"));
      setName("");
      refetch();
    } catch (err: unknown) {
      setNameMsg(err instanceof Error ? err.message : t("updateFailed"));
    } finally {
      setNameLoading(false);
    }
  }

  async function handlePasswordChange(e: React.FormEvent) {
    e.preventDefault();
    setPwError("");
    setPwMsg("");

    if (newPw.length < 6) {
      setPwError(t("passwordMinLength"));
      return;
    }
    if (newPw !== confirmPw) {
      setPwError(t("passwordMismatch"));
      return;
    }

    setPwLoading(true);
    try {
      await changePassword(currentPw, newPw);
      setPwMsg(t("passwordUpdated"));
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
    } catch (err: unknown) {
      setPwError(err instanceof Error ? err.message : t("passwordChangeFailed"));
    } finally {
      setPwLoading(false);
    }
  }

  return (
    <div className="p-10 max-w-xl space-y-8">
      <h1 className="text-xl font-semibold text-foreground tracking-tight">{t("title")}</h1>

      {/* Profile */}
      <div className="border border-border rounded-lg p-5 space-y-4">
        <h2 className="text-sm font-medium text-foreground">{t("profile")}</h2>
        <div>
          <label className="text-xs text-muted">{t("emailLabel")}</label>
          <p className="text-sm text-foreground mt-0.5">{user?.email}</p>
        </div>
        <form onSubmit={handleNameSave} className="space-y-3">
          <div>
            <label className="text-xs text-muted">{t("nameLabel")}</label>
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
              className="px-4 py-2 bg-accent hover:bg-accent-hover disabled:opacity-40 text-white text-xs font-medium rounded-md transition-colors"
            >
              {nameLoading ? tc("saving") : tc("save")}
            </button>
            {nameMsg && <span className="text-xs text-green-400">{nameMsg}</span>}
          </div>
        </form>
      </div>

      {/* Change Password */}
      <div className="border border-border rounded-lg p-5 space-y-4">
        <h2 className="text-sm font-medium text-foreground">{t("changePassword")}</h2>
        <form onSubmit={handlePasswordChange} className="space-y-3">
          {pwError && (
            <div className="border border-red-500/30 text-red-400 rounded-md px-3 py-2 text-xs">
              {pwError}
            </div>
          )}
          {pwMsg && (
            <div className="border border-green-500/30 text-green-400 rounded-md px-3 py-2 text-xs">
              {pwMsg}
            </div>
          )}
          <input
            type="password"
            placeholder={t("currentPassword")}
            value={currentPw}
            onChange={(e) => setCurrentPw(e.target.value)}
            required
            className={inputClass}
          />
          <input
            type="password"
            placeholder={t("newPassword")}
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            required
            minLength={6}
            className={inputClass}
          />
          <input
            type="password"
            placeholder={t("confirmNewPassword")}
            value={confirmPw}
            onChange={(e) => setConfirmPw(e.target.value)}
            required
            minLength={6}
            className={inputClass}
          />
          <button
            type="submit"
            disabled={pwLoading}
            className="px-4 py-2 bg-accent hover:bg-accent-hover disabled:opacity-40 text-white text-xs font-medium rounded-md transition-colors"
          >
            {pwLoading ? t("changing") : t("changePasswordBtn")}
          </button>
        </form>
      </div>

      {/* Logout */}
      <button
        onClick={logout}
        className="text-sm text-muted hover:text-red-400 transition-colors"
      >
        {tc("logoutFull")}
      </button>
    </div>
  );
}
