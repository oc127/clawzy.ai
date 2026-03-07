"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useAgents } from "@/hooks/useAgent";

const STATUS_DOT: Record<string, string> = {
  running: "bg-green-500",
  stopped: "bg-neutral-500",
  creating: "bg-yellow-500 animate-pulse",
  error: "bg-red-500",
};

export default function AgentsPage() {
  const t = useTranslations("agents");
  const tc = useTranslations("common");
  const { agents, loading, startAgent, stopAgent, deleteAgent } = useAgents();
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

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

  async function handleStart(id: string) {
    setActionLoading(id);
    try {
      await startAgent(id);
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : t("startFailed"));
    } finally {
      setActionLoading(null);
    }
  }

  async function handleStop(id: string) {
    setActionLoading(id);
    try {
      await stopAgent(id);
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : t("stopFailed"));
    } finally {
      setActionLoading(null);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm(t("confirmDelete"))) return;
    try {
      await deleteAgent(id);
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "Delete failed");
    }
  }

  if (loading) return <div className="p-10 text-sm text-muted">{tc("loading")}</div>;

  return (
    <div className="p-10 max-w-3xl">
      <h1 className="text-xl font-semibold text-foreground tracking-tight mb-8">{t("title")}</h1>

      {errorMsg && (
        <div className="mb-4 px-4 py-2.5 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center justify-between">
          <span className="text-xs text-red-400">{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-xs text-red-400 hover:text-red-300 ml-4">×</button>
        </div>
      )}

      {agents.length === 0 ? (
        <p className="text-sm text-muted">{t("noLobster")}</p>
      ) : (
        <div className="space-y-2">
          {agents.map((agent) => {
            const dot = STATUS_DOT[agent.status] || STATUS_DOT.stopped;
            const label = statusLabels[agent.status] || statusLabels.stopped;
            const isLoading = actionLoading === agent.id;
            const isRunning = agent.status === "running";
            const canStart = agent.status === "stopped" || agent.status === "error";

            return (
              <div
                key={agent.id}
                className="border border-border rounded-lg px-5 py-4"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${dot}`} />
                    <div>
                      <h3 className="text-sm font-medium text-foreground">{agent.name}</h3>
                      <p className="text-xs text-muted mt-0.5">
                        {t("brainLabel", { brain: brainLabels[agent.model_name] || agent.model_name })}
                        {" · "}
                        {label}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {canStart && (
                      <button
                        onClick={() => handleStart(agent.id)}
                        disabled={isLoading}
                        className="px-3 py-1.5 text-xs font-medium text-foreground border border-border rounded-md hover:bg-surface disabled:opacity-40 transition-colors"
                      >
                        {isLoading ? t("starting") : t("start")}
                      </button>
                    )}
                    {isRunning && (
                      <button
                        onClick={() => handleStop(agent.id)}
                        disabled={isLoading}
                        className="px-3 py-1.5 text-xs font-medium text-foreground border border-border rounded-md hover:bg-surface disabled:opacity-40 transition-colors"
                      >
                        {isLoading ? t("stopping") : t("stop")}
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(agent.id)}
                      className="px-3 py-1.5 text-xs text-red-400 hover:text-red-300 transition-colors"
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
