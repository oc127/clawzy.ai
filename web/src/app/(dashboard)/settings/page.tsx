"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/auth-context";
import { useLanguage } from "@/context/language-context";
import { apiPatch, apiGet, apiPost, ApiError } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Shield, AlertCircle, User, Info, Lock, Bell } from "lucide-react";

interface TodayUsage { used_today: number; daily_limit: number | null; }
interface PushSettings { push_channels: string[]; line_user_id: string | null; push_quiet_start: number | null; push_quiet_end: number | null; }

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const { t } = useLanguage();
  const [name, setName] = useState(user?.name ?? "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url ?? "");
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [savingPw, setSavingPw] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dailyLimit, setDailyLimit] = useState<string>(
    user?.daily_credit_limit ? String(user.daily_credit_limit) : ""
  );
  const [savingLimit, setSavingLimit] = useState(false);
  const [todayUsage, setTodayUsage] = useState<TodayUsage | null>(null);
  const [pushSettings, setPushSettings] = useState<PushSettings | null>(null);
  const [savingPush, setSavingPush] = useState(false);

  useEffect(() => {
    setName(user?.name ?? "");
    setAvatarUrl(user?.avatar_url ?? "");
    setDailyLimit(user?.daily_credit_limit ? String(user.daily_credit_limit) : "");
  }, [user]);

  useEffect(() => {
    apiGet<TodayUsage>("/billing/credits/today").then(setTodayUsage).catch(() => {});
    apiGet<PushSettings>("/lucy/push-channels").then(setPushSettings).catch(() => {});
  }, []);

  if (!user) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await apiPatch("/users/me", { name: name || undefined, avatar_url: avatarUrl || undefined });
      await refreshUser();
      toast.success("Settings saved");
    } catch {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPw !== confirmPw) { toast.error(t.settings.passwordMismatch); return; }
    setSavingPw(true);
    try {
      await apiPost("/auth/change-password", { current_password: currentPw, new_password: newPw });
      toast.success(t.settings.passwordChanged);
      setCurrentPw(""); setNewPw(""); setConfirmPw("");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : t.settings.passwordChangeFailed);
    } finally {
      setSavingPw(false);
    }
  };

  const handleSaveLimit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingLimit(true);
    try {
      const limit = dailyLimit ? parseInt(dailyLimit, 10) : 0;
      if (dailyLimit && (isNaN(limit) || limit < 0)) { toast.error("Please enter a valid number"); return; }
      await apiPatch("/users/me", { daily_credit_limit: limit || 0 });
      await refreshUser();
      toast.success(limit > 0 ? `Daily limit set to ${limit} credits` : "Daily limit removed");
    } catch {
      toast.error("Failed to save limit");
    } finally {
      setSavingLimit(false);
    }
  };

  const limitValue = dailyLimit ? parseInt(dailyLimit, 10) : 0;
  const usedToday = todayUsage?.used_today ?? 0;
  const usagePercent = limitValue > 0 ? Math.min((usedToday / limitValue) * 100, 100) : 0;

  const initials = user.name
    ? user.name.split(" ").map((n: string) => n[0]).join("").toUpperCase().slice(0, 2)
    : user.email[0].toUpperCase();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-[#222222] dark:text-white">Settings</h1>
        <p className="mt-0.5 text-[#717171] dark:text-[#a0a0a0]">Manage your account and preferences.</p>
      </div>

      <div className="max-w-lg space-y-5">
        {/* Profile */}
        <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-6 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-red shadow-sm">
              <User className="h-4 w-4 text-white" />
            </div>
            <h2 className="text-base font-bold text-[#222222] dark:text-white">Profile</h2>
          </div>

          {/* Avatar preview */}
          <div className="mb-5 flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl icon-gradient-red shadow-md text-white text-xl font-bold">
              {initials}
            </div>
            <div>
              <p className="font-semibold text-[#222222] dark:text-white">{user.name}</p>
              <p className="text-sm text-[#717171] dark:text-[#a0a0a0]">{user.email}</p>
            </div>
          </div>

          <form onSubmit={handleSave} className="space-y-4">
            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222] dark:text-white">Display Name</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
            </div>
            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222] dark:text-white">Avatar URL</label>
              <Input value={avatarUrl} onChange={(e) => setAvatarUrl(e.target.value)} placeholder="https://example.com/avatar.png" />
            </div>
            <Button
              type="submit"
              loading={saving}
              className="bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl font-semibold shadow-sm"
            >
              Save Changes
            </Button>
          </form>
        </div>

        {/* Change Password */}
        <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-6 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-orange shadow-sm">
              <Lock className="h-4 w-4 text-white" />
            </div>
            <h2 className="text-base font-bold text-[#222222] dark:text-white">{t.settings.changePassword}</h2>
          </div>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222] dark:text-white">{t.settings.currentPassword}</label>
              <Input type="password" value={currentPw} onChange={(e) => setCurrentPw(e.target.value)} placeholder="••••••••" required />
            </div>
            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222] dark:text-white">{t.settings.newPassword}</label>
              <Input type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} placeholder="••••••••" minLength={8} required />
            </div>
            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222] dark:text-white">{t.settings.confirmPassword}</label>
              <Input type="password" value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)} placeholder="••••••••" minLength={8} required />
            </div>
            <Button
              type="submit"
              loading={savingPw}
              disabled={!currentPw || !newPw || !confirmPw}
              className="bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl font-semibold shadow-sm"
            >
              {t.settings.changePassword}
            </Button>
          </form>
        </div>

        {/* Budget Manager */}
        <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-6 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-orange shadow-sm">
              <Shield className="h-4 w-4 text-white" />
            </div>
            <h2 className="text-base font-bold text-[#222222] dark:text-white">Budget Manager</h2>
          </div>
          <p className="mb-4 text-sm text-[#717171] dark:text-[#a0a0a0]">
            Set a daily credit limit to control spending. When the limit is reached,
            your agents will pause until the next day.
          </p>
          <form onSubmit={handleSaveLimit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-[#222222] dark:text-white">Daily Credit Limit</label>
              <Input
                type="number"
                min="0"
                value={dailyLimit}
                onChange={(e) => setDailyLimit(e.target.value)}
                placeholder="No limit (enter amount to set)"
              />
              <p className="text-xs text-[#b0b0b0] dark:text-[#666]">Leave empty or 0 to remove the limit.</p>
            </div>

            {limitValue > 0 && (
              <div className="rounded-xl bg-[#f7f7f7] dark:bg-[#262626] border border-[#ebebeb] dark:border-[#333] p-4">
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="text-[#717171] dark:text-[#a0a0a0]">Today&apos;s usage</span>
                  <span className="font-semibold">
                    <span className={usagePercent >= 100 ? "text-[#ff385c]" : "text-[#222222] dark:text-white"}>
                      {usedToday}
                    </span>
                    <span className="text-[#717171] dark:text-[#a0a0a0]"> / {limitValue} credits</span>
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-[#ebebeb] dark:bg-[#333]">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      usagePercent >= 100 ? "bg-[#ff385c]" : usagePercent >= 80 ? "bg-amber-500" : "bg-[#ff385c]"
                    }`}
                    style={{ width: `${usagePercent}%` }}
                  />
                </div>
                {usagePercent >= 100 && (
                  <div className="mt-2 flex items-center gap-1.5 text-xs text-[#ff385c]">
                    <AlertCircle className="h-3 w-3" />
                    Daily limit reached. Agents paused until tomorrow.
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-2">
              <Button
                type="submit"
                loading={savingLimit}
                className="bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl font-semibold shadow-sm"
              >
                Save Limit
              </Button>
              {user.daily_credit_limit && (
                <Button
                  type="button"
                  variant="ghost"
                  className="text-[#717171] dark:text-[#a0a0a0] hover:bg-[#f7f7f7] dark:hover:bg-[#262626] rounded-xl"
                  onClick={() => {
                    setDailyLimit("");
                    apiPatch("/users/me", { daily_credit_limit: 0 })
                      .then(() => { refreshUser(); toast.success("Daily limit removed"); })
                      .catch(() => toast.error("Failed to remove limit"));
                  }}
                >
                  Remove Limit
                </Button>
              )}
            </div>
          </form>
        </div>

        {/* Push Notification Settings */}
        {pushSettings && (
          <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-6 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-pink shadow-sm">
                <Bell className="h-4 w-4 text-white" />
              </div>
              <h2 className="text-base font-bold text-[#222222] dark:text-white">Push Notifications</h2>
            </div>
            <p className="mb-4 text-sm text-[#717171] dark:text-[#a0a0a0]">
              Choose how Lucy reaches you when she has something to say.
            </p>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="block text-sm font-semibold text-[#222222] dark:text-white">Channels</label>
                {["websocket", "line", "email"].map((ch) => (
                  <label key={ch} className="flex items-center gap-3 py-1.5">
                    <input
                      type="checkbox"
                      checked={pushSettings.push_channels.includes(ch)}
                      onChange={(e) => {
                        const channels = e.target.checked
                          ? [...pushSettings.push_channels, ch]
                          : pushSettings.push_channels.filter((c) => c !== ch);
                        setPushSettings({ ...pushSettings, push_channels: channels });
                      }}
                      className="h-4 w-4 rounded border-[#dddddd] text-[#ff385c] focus:ring-[#ff385c]"
                    />
                    <span className="text-sm text-[#222222] dark:text-white capitalize">{ch === "websocket" ? "In-app (WebSocket)" : ch === "line" ? "LINE" : "Email"}</span>
                  </label>
                ))}
              </div>

              {pushSettings.push_channels.includes("line") && (
                <div className="space-y-1.5">
                  <label className="block text-sm font-semibold text-[#222222] dark:text-white">LINE User ID</label>
                  <Input
                    value={pushSettings.line_user_id ?? ""}
                    onChange={(e) => setPushSettings({ ...pushSettings, line_user_id: e.target.value || null })}
                    placeholder="U1234567890abcdef..."
                  />
                </div>
              )}

              <div className="space-y-1.5">
                <label className="block text-sm font-semibold text-[#222222] dark:text-white">Quiet Hours</label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min={0}
                    max={23}
                    value={pushSettings.push_quiet_start ?? ""}
                    onChange={(e) => setPushSettings({ ...pushSettings, push_quiet_start: e.target.value ? parseInt(e.target.value) : null })}
                    placeholder="Start (0-23)"
                    className="w-28"
                  />
                  <span className="text-sm text-[#717171] dark:text-[#a0a0a0]">to</span>
                  <Input
                    type="number"
                    min={0}
                    max={23}
                    value={pushSettings.push_quiet_end ?? ""}
                    onChange={(e) => setPushSettings({ ...pushSettings, push_quiet_end: e.target.value ? parseInt(e.target.value) : null })}
                    placeholder="End (0-23)"
                    className="w-28"
                  />
                </div>
                <p className="text-xs text-[#b0b0b0] dark:text-[#666]">Lucy won&apos;t send notifications during these hours.</p>
              </div>

              <Button
                onClick={async () => {
                  setSavingPush(true);
                  try {
                    await apiPatch("/lucy/push-channels", pushSettings);
                    toast.success("Notification settings saved");
                  } catch {
                    toast.error("Failed to save notification settings");
                  } finally {
                    setSavingPush(false);
                  }
                }}
                loading={savingPush}
                className="bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl font-semibold shadow-sm"
              >
                Save Notifications
              </Button>
            </div>
          </div>
        )}

        {/* Account Info */}
        <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-6 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-blue shadow-sm">
              <Info className="h-4 w-4 text-white" />
            </div>
            <h2 className="text-base font-bold text-[#222222] dark:text-white">Account Info</h2>
          </div>
          <div className="space-y-3">
            {[
              { label: "Email", value: user.email },
              { label: "Member since", value: new Date(user.created_at).toLocaleDateString() },
              { label: "Credit Balance", value: `${user.credit_balance} credits` },
              { label: "Daily Limit", value: user.daily_credit_limit ? `${user.daily_credit_limit} credits` : "Unlimited" },
            ].map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between py-2 border-b border-[#f7f7f7] dark:border-[#333] last:border-0">
                <span className="text-sm text-[#717171] dark:text-[#a0a0a0]">{label}</span>
                <span className="text-sm font-semibold text-[#222222] dark:text-white">{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
