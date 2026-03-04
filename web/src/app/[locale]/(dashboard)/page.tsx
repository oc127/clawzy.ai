"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { listAgents, createAgent, type Agent } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

const STATUS_DOT: Record<string, string> = {
  running: "bg-green-500",
  stopped: "bg-neutral-500",
  creating: "bg-yellow-500 animate-pulse",
  error: "bg-red-500",
};

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const t = useTranslations("dashboard");
  const tc = useTranslations("common");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const statusLabels: Record<string, string> = {
    running: t("statusRunning"),
    stopped: t("statusStopped"),
    creating: t("statusCreating"),
    error: t("statusError"),
  };

  useEffect(() => {
    listAgents()
      .then(setAgents)
      .finally(() => setLoading(false));
  }, []);

  async function handleCreateAgent() {
    setCreating(true);
    try {
      const agent = await createAgent("My Lobster", "deepseek-chat");
      setAgents((prev) => [agent, ...prev]);
    } catch {
      // ignore
    } finally {
      setCreating(false);
    }
  }

  if (loading) {
    return <div className="p-10 text-sm text-muted">{tc("loading")}</div>;
  }

  return (
    <div className="p-10 max-w-3xl">
      <div className="flex items-center justify-between mb-10">
        <div>
          <h1 className="text-xl font-semibold text-foreground tracking-tight">
            {t("hello", { name: user?.name ?? "" })}
          </h1>
          <p className="text-sm text-muted mt-1">{t("energyCount", { balance: user?.credit_balance ?? 0 })}</p>
        </div>
        {agents.length === 0 && (
          <button
            onClick={handleCreateAgent}
            disabled={creating}
            className="px-5 py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {creating ? t("hatching") : t("createMyLobster")}
          </button>
        )}
      </div>

      {agents.length === 0 ? (
        <div className="text-center py-24">
          <h2 className="text-lg font-medium text-foreground mb-2">
            {t("noLobsterYet")}
          </h2>
          <p className="text-sm text-muted mb-8">{t("noLobsterDesc")}</p>
          <button
            onClick={handleCreateAgent}
            disabled={creating}
            className="px-6 py-3 bg-accent hover:bg-accent-hover disabled:opacity-40 text-white font-medium rounded-lg transition-colors"
          >
            {creating ? t("hatchingLobster") : t("createFirstLobster")}
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {agents.map((agent) => {
            const dot = STATUS_DOT[agent.status] || STATUS_DOT.stopped;
            const label = statusLabels[agent.status] || statusLabels.stopped;
            return (
              <div
                key={agent.id}
                onClick={() => router.push(`/chat/${agent.id}`)}
                className="border border-border rounded-lg px-5 py-4 cursor-pointer hover:bg-surface transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${dot}`} />
                    <div>
                      <h3 className="text-sm font-medium text-foreground">{agent.name}</h3>
                      <p className="text-xs text-muted mt-0.5">
                        {t("brainLabel", { brain: agent.model_name })}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs text-muted">{label}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
