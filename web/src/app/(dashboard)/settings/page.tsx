"use client";

import { useState } from "react";
import { useAuth } from "@/context/auth-context";
import { apiPatch } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [name, setName] = useState(user?.name ?? "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url ?? "");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  if (!user) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      await apiPatch("/users/me", {
        name: name || undefined,
        avatar_url: avatarUrl || undefined,
      });
      await refreshUser();
      setMessage("Settings saved.");
    } catch {
      setMessage("Failed to save settings.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">Settings</h1>
      <p className="mb-8 text-muted-foreground">Manage your account settings.</p>

      <div className="max-w-lg space-y-6">
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
            {message && (
              <p className="text-sm text-muted-foreground">{message}</p>
            )}
            <Button type="submit" disabled={saving}>
              {saving ? "Saving..." : "Save"}
            </Button>
          </form>
        </Card>

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
          </div>
        </Card>
      </div>
    </div>
  );
}
