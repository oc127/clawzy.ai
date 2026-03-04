"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { listAgents, createAgent, type Agent } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

const STATUS_COLORS: Record<string, string> = {
  running: "text-green-400",
  stopped: "text-gray-400",
  creating: "text-yellow-400",
  error: "text-red-400",
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
    return (
      <div className="p-8 text-gray-400">{tc("loading")}</div>
    );
  }

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {t("hello", { name: user?.name ?? "" })}
          </h1>
          <p className="text-gray-500 mt-1">{t("energyCount", { balance: user?.credit_balance ?? 0 })}</p>
        </div>
        {agents.length === 0 && (
          <button
            onClick={handleCreateAgent}
            disabled={creating}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-xl transition"
          >
            {creating ? t("hatching") : t("createMyLobster")}
          </button>
        )}
      </div>

      {agents.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-6xl mb-4">🦞</div>
          <h2 className="text-xl font-semibold text-white mb-2">
            {t("noLobsterYet")}
          </h2>
          <p className="text-gray-500 mb-6">
            {t("noLobsterDesc")}
          </p>
          <button
            onClick={handleCreateAgent}
            disabled={creating}
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white text-lg font-semibold rounded-xl transition"
          >
            {creating ? t("hatchingLobster") : t("createFirstLobster")}
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {agents.map((agent) => {
            const color = STATUS_COLORS[agent.status] || STATUS_COLORS.stopped;
            const label = statusLabels[agent.status] || statusLabels.stopped;
            return (
              <div
                key={agent.id}
                onClick={() => router.push(`/chat/${agent.id}`)}
                className="bg-gray-900 border border-gray-800 rounded-xl p-6 cursor-pointer hover:border-gray-600 transition"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="text-3xl">🦞</div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">
                        {agent.name}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {t("brainLabel", { brain: agent.model_name })}
                      </p>
                    </div>
                  </div>
                  <div className={`text-sm font-medium ${color}`}>
                    {label}
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
