"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useAuth } from "@/hooks/useAuth";
import { useAgents } from "@/hooks/useAgent";
import { listModels, type ModelInfo } from "@/lib/api";
import AgentCard from "@/components/dashboard/AgentCard";
import CreditsBadge from "@/components/dashboard/CreditsBadge";

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const t = useTranslations("dashboard");
  const tc = useTranslations("common");
  const { agents, loading, createAgent } = useAgents();
  const [creating, setCreating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState("deepseek-chat");

  const statusLabels: Record<string, string> = {
    running: t("statusRunning"),
    stopped: t("statusStopped"),
    creating: t("statusCreating"),
    error: t("statusError"),
  };

  useEffect(() => {
    listModels()
      .then((data) => {
        const list = Array.isArray(data) ? data : [];
        setModels(list);
        if (list.length > 0 && !list.find((m) => m.id === selectedModel)) {
          setSelectedModel(list[0].id);
        }
      })
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCreateAgent() {
    setCreating(true);
    try {
      await createAgent("My Lobster", selectedModel);
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "Failed to create lobster");
    } finally {
      setCreating(false);
    }
  }

  if (loading) {
    return <div className="p-10 text-sm text-muted">{tc("loading")}</div>;
  }

  const createSection = (
    <>
      {models.length > 1 && (
        <select
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          className="px-3 py-2.5 bg-surface border border-border rounded-lg text-foreground text-sm focus:outline-none focus:border-accent transition-colors"
        >
          {models.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name} ({m.tier})
            </option>
          ))}
        </select>
      )}
      <button
        onClick={handleCreateAgent}
        disabled={creating}
        className="px-5 py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
      >
        {creating ? t("hatching") : t("createMyLobster")}
      </button>
    </>
  );

  return (
    <div className="p-10 max-w-3xl">
      {errorMsg && (
        <div className="mb-4 px-4 py-2.5 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center justify-between">
          <span className="text-xs text-red-400">{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-xs text-red-400 hover:text-red-300 ml-4">×</button>
        </div>
      )}
      <div className="flex items-center justify-between mb-10">
        <div>
          <h1 className="text-xl font-semibold text-foreground tracking-tight">
            {t("hello", { name: user?.name ?? "" })}
          </h1>
          <p className="text-sm text-muted mt-1">
            <CreditsBadge balance={user?.credit_balance ?? 0} label={tc("energy")} />
          </p>
        </div>
        {agents.length === 0 && (
          <div className="flex items-center gap-2">
            {createSection}
          </div>
        )}
      </div>

      {agents.length === 0 ? (
        <div className="text-center py-20">
          {/* Breathing lobster silhouette */}
          <div className="animate-breathe mb-6">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" className="mx-auto opacity-40">
              <path d="M32 8c-4 0-8 2-10 6-3 0-6 2-7 5s0 6 2 8c-2 3-3 6-2 9 1 4 4 6 8 7 1 3 4 6 9 6s8-3 9-6c4-1 7-3 8-7 1-3 0-6-2-9 2-2 3-5 2-8s-4-5-7-5c-2-4-6-6-10-6z" fill="currentColor" className="text-accent/30"/>
              <circle cx="26" cy="24" r="2" fill="currentColor" className="text-accent/50"/>
              <circle cx="38" cy="24" r="2" fill="currentColor" className="text-accent/50"/>
              <path d="M14 20c-4-2-8-1-10 1M50 20c4-2 8-1 10 1M14 22c-5-1-9 1-10 4M50 22c5-1 9 1 10 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="text-accent/20"/>
            </svg>
          </div>
          <h2 className="text-lg font-medium text-foreground mb-2">
            {t("noLobsterYet")}
          </h2>
          <p className="text-sm text-muted mb-8">{t("noLobsterDesc")}</p>
          <div className="flex items-center justify-center gap-2">
            {models.length > 1 && (
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="px-3 py-3 bg-surface border border-border rounded-lg text-foreground text-sm transition-colors"
              >
                {models.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.tier})
                  </option>
                ))}
              </select>
            )}
            <button
              onClick={handleCreateAgent}
              disabled={creating}
              className="px-6 py-3 bg-accent hover:bg-accent-hover disabled:opacity-40 text-white font-medium rounded-lg transition-all duration-300 hover:shadow-[0_0_20px_rgba(79,110,247,0.2)]"
            >
              {creating ? t("hatchingLobster") : t("createFirstLobster")}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {agents.map((agent) => (
            <AgentCard
              key={agent.id}
              name={agent.name}
              modelName={agent.model_name}
              status={agent.status}
              brainLabel={t("brainLabel", { brain: agent.model_name })}
              statusLabel={statusLabels[agent.status] || statusLabels.stopped}
              onClick={() => router.push(`/chat/${agent.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
