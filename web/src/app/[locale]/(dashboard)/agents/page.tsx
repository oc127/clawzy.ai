"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { listAgents, deleteAgent, startAgent, stopAgent, type Agent } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  running: "text-green-400",
  stopped: "text-gray-400",
  creating: "text-yellow-400",
  error: "text-red-400",
};

export default function AgentsPage() {
  const t = useTranslations("agents");
  const tc = useTranslations("common");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const statusLabels: Record<string, string> = {
    running: t("statusRunning"),
    stopped: t("statusStopped"),
    creating: t("statusCreating"),
    error: t("statusError"),
  };

  const brainLabels: Record<string, string> = {
    "qwen-turbo": t("brainQwen"),
    "deepseek-chat": t("brainDeepseek"),
    "claude-sonnet": t("brainClaude"),
    "gpt-4o": t("brainGpt4o"),
  };

  useEffect(() => {
    listAgents()
      .then(setAgents)
      .finally(() => setLoading(false));
  }, []);

  async function handleStart(id: string) {
    setActionLoading(id);
    try {
      const updated = await startAgent(id);
      setAgents((prev) => prev.map((a) => (a.id === id ? updated : a)));
    } catch (e: any) {
      alert(e.message || t("startFailed"));
    } finally {
      setActionLoading(null);
    }
  }

  async function handleStop(id: string) {
    setActionLoading(id);
    try {
      const updated = await stopAgent(id);
      setAgents((prev) => prev.map((a) => (a.id === id ? updated : a)));
    } catch (e: any) {
      alert(e.message || t("stopFailed"));
    } finally {
      setActionLoading(null);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm(t("confirmDelete"))) return;
    await deleteAgent(id);
    setAgents((prev) => prev.filter((a) => a.id !== id));
  }

  if (loading) return <div className="p-8 text-gray-400">{tc("loading")}</div>;

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-white mb-8">{t("title")}</h1>

      {agents.length === 0 ? (
        <p className="text-gray-500">{t("noLobster")}</p>
      ) : (
        <div className="space-y-4">
          {agents.map((agent) => {
            const color = STATUS_COLORS[agent.status] || STATUS_COLORS.stopped;
            const label = statusLabels[agent.status] || statusLabels.stopped;
            const isLoading = actionLoading === agent.id;
            const isRunning = agent.status === "running";
            const canStart = agent.status === "stopped" || agent.status === "error";

            return (
              <div
                key={agent.id}
                className="bg-gray-900 border border-gray-800 rounded-xl p-6"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="text-3xl relative">
                      {isRunning && (
                        <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                      )}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">
                        {agent.name}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {t("brainLabel", { brain: brainLabels[agent.model_name] || agent.model_name })}
                      </p>
                      <p className={`text-sm ${color}`}>
                        {label}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {canStart && (
                      <button
                        onClick={() => handleStart(agent.id)}
                        disabled={isLoading}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition"
                      >
                        {isLoading ? t("starting") : t("start")}
                      </button>
                    )}
                    {isRunning && (
                      <button
                        onClick={() => handleStop(agent.id)}
                        disabled={isLoading}
                        className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition"
                      >
                        {isLoading ? t("stopping") : t("stop")}
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(agent.id)}
                      className="text-sm text-red-400 hover:text-red-300"
                    >
                      {tc("delete")}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
