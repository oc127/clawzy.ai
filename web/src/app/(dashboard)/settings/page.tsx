"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/auth-context";
import { apiPatch, apiGet } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Shield, AlertCircle } from "lucide-react";

interface TodayUsage {
  used_today: number;
  daily_limit: number | null;
}

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [name, setName] = useState(user?.name ?? "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url ?? "");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setName(user?.name ?? "");
    setAvatarUrl(user?.avatar_url ?? "");
    setDailyLimit(user?.daily_credit_limit ? String(user.daily_credit_limit) : "");
  }, [user]);

  // Budget manager state
  const [dailyLimit, setDailyLimit] = useState<string>(
    user?.daily_credit_limit ? String(user.daily_credit_limit) : ""
  );
  const [savingLimit, setSavingLimit] = useState(false);
  const [todayUsage, setTodayUsage] = useState<TodayUsage | null>(null);

  useEffect(() => {
    apiGet<TodayUsage>("/billing/credits/today")
      .then(setTodayUsage)
      .catch(() => {});
  }, []);

  if (!user) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await apiPatch("/users/me", {
        name: name || undefined,
        avatar_url: avatarUrl || undefined,
      });
      await refreshUser();
      toast.success("Settings saved");
    } catch {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveLimit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingLimit(true);
    try {
      const limit = dailyLimit ? parseInt(dailyLimit, 10) : 0;
      if (dailyLimit && (isNaN(limit) || limit < 0)) {
        toast.error("Please enter a valid number");
        setSavingLimit(false);
        return;
      }
      await apiPatch("/users/me", {
        daily_credit_limit: limit || 0,  // 0 = remove limit
      });
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

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">Settings</h1>
      <p className="mb-8 text-muted-foreground">Manage your account settings.</p>

      <div className="max-w-lg space-y-6">
        {/* Profile */}
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Profile</h2>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm text-muted-foreground">
                Name
              </label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-muted-foreground">
                Avatar URL
              </label>
              <Input
                value={avatarUrl}
                onChange={(e) => setAvatarUrl(e.target.value)}
                placeholder="https://example.com/avatar.png"
              />
            </div>
            <Button type="submit" loading={saving}>
              Save
            </Button>
          </form>
        </Card>

        {/* Budget Manager */}
        <Card>
          <div className="mb-4 flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Budget Manager</h2>
          </div>
          <p className="mb-4 text-sm text-muted-foreground">
            Set a daily credit limit to control spending. When the limit is reached,
            your agents will pause until the next day.
          </p>
          <form onSubmit={handleSaveLimit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm text-muted-foreground">
                Daily Credit Limit
              </label>
              <Input
                type="number"
                min="0"
                value={dailyLimit}
                onChange={(e) => setDailyLimit(e.target.value)}
                placeholder="No limit (enter amount to set)"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Leave empty or set to 0 to remove the limit.
              </p>
            </div>

            {/* Usage indicator */}
            {limitValue > 0 && (
              <div className="rounded-lg bg-muted/50 p-3">
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Today&apos;s usage</span>
                  <span>
                    <span className={usagePercent >= 100 ? "text-red-400 font-semibold" : ""}>
                      {usedToday}
                    </span>
                    {" / "}
                    {limitValue} credits
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-muted">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      usagePercent >= 100
                        ? "bg-red-500"
                        : usagePercent >= 80
                          ? "bg-yellow-500"
                          : "bg-primary"
                    }`}
                    style={{ width: `${usagePercent}%` }}
                  />
                </div>
                {usagePercent >= 100 && (
                  <div className="mt-2 flex items-center gap-1 text-xs text-red-400">
                    <AlertCircle className="h-3 w-3" />
                    Daily limit reached. Agents paused until tomorrow.
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-2">
              <Button type="submit" loading={savingLimit}>
                Save Limit
              </Button>
              {user.daily_credit_limit && (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setDailyLimit("");
                    apiPatch("/users/me", { daily_credit_limit: 0 })
                      .then(() => {
                        refreshUser();
                        toast.success("Daily limit removed");
                      })
                      .catch(() => toast.error("Failed to remove limit"));
                  }}
                >
                  Remove Limit
                </Button>
              )}
            </div>
          </form>
        </Card>

        {/* Account Info */}
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Account Info</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Email</span>
              <span>{user.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Member since</span>
              <span>{new Date(user.created_at).toLocaleDateString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Credit Balance</span>
              <span>{user.credit_balance}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Daily Limit</span>
              <span>{user.daily_credit_limit ?? "Unlimited"}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
