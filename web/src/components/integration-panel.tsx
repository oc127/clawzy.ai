"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import {
  createIntegration,
  deleteIntegration,
  getIntegrations,
  updateIntegration,
} from "@/lib/api";
import type { Integration } from "@/lib/types";
import { toast } from "sonner";
import {
  ChevronDown,
  ChevronUp,
  Copy,
  ExternalLink,
  Link2,
  Plus,
  ToggleLeft,
  ToggleRight,
  Trash2,
} from "lucide-react";

const PLATFORMS = [
  {
    id: "line" as const,
    name: "LINE",
    color: "bg-green-500",
    fields: [
      { key: "channel_secret", label: "Channel Secret", placeholder: "Your LINE channel secret" },
      { key: "channel_access_token", label: "Channel Access Token", placeholder: "Your LINE channel access token" },
    ],
    docUrl: "https://developers.line.biz/en/docs/messaging-api/",
  },
  {
    id: "discord" as const,
    name: "Discord",
    color: "bg-indigo-500",
    fields: [
      { key: "bot_token", label: "Bot Token", placeholder: "Your Discord bot token" },
    ],
    docUrl: "https://discord.com/developers/docs/intro",
  },
  {
    id: "telegram" as const,
    name: "Telegram",
    color: "bg-blue-500",
    fields: [
      { key: "bot_token", label: "Bot Token", placeholder: "Your Telegram bot token from @BotFather" },
    ],
    docUrl: "https://core.telegram.org/bots",
  },
];

function PlatformIcon({ platform }: { platform: string }) {
  if (platform === "line") {
    return (
      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63h2.386c.349 0 .63.285.63.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63.349 0 .631.285.631.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314" />
      </svg>
    );
  }
  if (platform === "discord") {
    return (
      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
      </svg>
    );
  }
  if (platform === "telegram") {
    return (
      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
      </svg>
    );
  }
  return <Link2 className="h-4 w-4" />;
}

export function IntegrationPanel({ agentId }: { agentId: string }) {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [showPanel, setShowPanel] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Integration | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    getIntegrations(agentId)
      .then(setIntegrations)
      .catch(() => {});
  }, [agentId]);

  const connectedPlatforms = new Set(integrations.map((i) => i.platform));
  const availablePlatforms = PLATFORMS.filter((p) => !connectedPlatforms.has(p.id));

  const handleAdd = async () => {
    if (!selectedPlatform) return;
    setSaving(true);
    try {
      const integration = await createIntegration(agentId, {
        platform: selectedPlatform,
        ...formData,
      });
      setIntegrations((prev) => [...prev, integration]);
      setShowAddForm(false);
      setSelectedPlatform(null);
      setFormData({});
      toast.success(`${selectedPlatform} integration added`);
    } catch (err: any) {
      toast.error(err.detail || "Failed to create integration");
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (integration: Integration) => {
    try {
      const updated = await updateIntegration(integration.id, {
        enabled: !integration.enabled,
      });
      setIntegrations((prev) =>
        prev.map((i) => (i.id === integration.id ? updated : i))
      );
      toast.success(`${integration.platform} ${updated.enabled ? "enabled" : "disabled"}`);
    } catch {
      toast.error("Failed to toggle integration");
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteIntegration(deleteTarget.id);
      setIntegrations((prev) => prev.filter((i) => i.id !== deleteTarget.id));
      toast.success(`${deleteTarget.platform} integration removed`);
    } catch {
      toast.error("Failed to remove integration");
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  };

  const copyWebhookUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    toast.success("Webhook URL copied");
  };

  const platformMeta = (id: string) => PLATFORMS.find((p) => p.id === id);

  return (
    <div className="border-t border-border pt-3 mt-3">
      <button
        onClick={() => setShowPanel(!showPanel)}
        className="flex w-full items-center justify-between text-sm font-semibold"
      >
        <span className="flex items-center gap-1.5">
          <Link2 className="h-3.5 w-3.5" />
          Integrations
          {integrations.length > 0 && (
            <span className="ml-1 rounded-full bg-primary/20 px-1.5 py-0.5 text-[10px] text-primary">
              {integrations.length}
            </span>
          )}
        </span>
        {showPanel ? (
          <ChevronUp className="h-3.5 w-3.5 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        )}
      </button>

      {showPanel && (
        <div className="mt-3 space-y-2">
          {/* Existing integrations */}
          {integrations.map((integration) => {
            const meta = platformMeta(integration.platform);
            return (
              <div
                key={integration.id}
                className="rounded-lg bg-muted/50 p-2.5"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`flex h-6 w-6 items-center justify-center rounded ${meta?.color || "bg-gray-500"} text-white`}>
                      <PlatformIcon platform={integration.platform} />
                    </div>
                    <span className="text-sm font-medium">{meta?.name || integration.platform}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleToggle(integration)}
                      className="rounded p-0.5 text-muted-foreground hover:text-foreground"
                      title={integration.enabled ? "Disable" : "Enable"}
                    >
                      {integration.enabled ? (
                        <ToggleRight className="h-4 w-4 text-green-400" />
                      ) : (
                        <ToggleLeft className="h-4 w-4" />
                      )}
                    </button>
                    <button
                      onClick={() => setDeleteTarget(integration)}
                      className="rounded p-0.5 text-muted-foreground hover:text-red-400"
                      title="Remove"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                {/* Webhook URL */}
                {integration.webhook_url && (
                  <div className="mt-2 flex items-center gap-1">
                    <code className="flex-1 truncate rounded bg-black/30 px-2 py-1 text-[10px] text-muted-foreground">
                      {integration.webhook_url}
                    </code>
                    <button
                      onClick={() => copyWebhookUrl(integration.webhook_url!)}
                      className="rounded p-1 text-muted-foreground hover:text-foreground"
                      title="Copy webhook URL"
                    >
                      <Copy className="h-3 w-3" />
                    </button>
                  </div>
                )}
              </div>
            );
          })}

          {/* Add new integration */}
          {!showAddForm && availablePlatforms.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              className="w-full h-7 text-xs"
              onClick={() => setShowAddForm(true)}
            >
              <Plus className="mr-1 h-3 w-3" />
              Add Integration
            </Button>
          )}

          {showAddForm && (
            <div className="rounded-lg border border-border p-3 space-y-3">
              {/* Platform selector */}
              {!selectedPlatform && (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">Select a platform:</p>
                  {availablePlatforms.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => setSelectedPlatform(p.id)}
                      className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent"
                    >
                      <div className={`flex h-6 w-6 items-center justify-center rounded ${p.color} text-white`}>
                        <PlatformIcon platform={p.id} />
                      </div>
                      <span>{p.name}</span>
                    </button>
                  ))}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full h-7 text-xs"
                    onClick={() => setShowAddForm(false)}
                  >
                    Cancel
                  </Button>
                </div>
              )}

              {/* Credential form */}
              {selectedPlatform && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <PlatformIcon platform={selectedPlatform} />
                    <span className="text-sm font-medium">
                      {platformMeta(selectedPlatform)?.name} Setup
                    </span>
                  </div>

                  {platformMeta(selectedPlatform)?.fields.map((field) => (
                    <div key={field.key}>
                      <label className="mb-1 block text-xs text-muted-foreground">
                        {field.label}
                      </label>
                      <Input
                        type="password"
                        placeholder={field.placeholder}
                        value={formData[field.key] || ""}
                        onChange={(e) =>
                          setFormData((prev) => ({ ...prev, [field.key]: e.target.value }))
                        }
                        className="h-8 text-xs"
                      />
                    </div>
                  ))}

                  <a
                    href={platformMeta(selectedPlatform)?.docUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-[10px] text-primary hover:underline"
                  >
                    <ExternalLink className="h-3 w-3" />
                    Setup guide
                  </a>

                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 text-xs flex-1"
                      onClick={() => {
                        setSelectedPlatform(null);
                        setFormData({});
                        setShowAddForm(false);
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      className="h-7 text-xs flex-1"
                      onClick={handleAdd}
                      loading={saving}
                    >
                      Connect
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}

          {integrations.length === 0 && !showAddForm && availablePlatforms.length === 0 && (
            <p className="text-xs text-muted-foreground">
              All platforms connected.
            </p>
          )}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Remove Integration"
        message={`Remove ${deleteTarget?.platform} integration? The bot will stop responding to messages from this platform.`}
        confirmLabel="Remove"
        variant="danger"
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
