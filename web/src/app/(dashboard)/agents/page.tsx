"use client";

import { useEffect, useState } from "react";
import { listAgents, deleteAgent, startAgent, stopAgent, type Agent } from "@/lib/api";

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  running: { label: "在线", color: "text-green-400" },
  stopped: { label: "休息中", color: "text-gray-400" },
  creating: { label: "创建中", color: "text-yellow-400" },
  error: { label: "不舒服", color: "text-red-400" },
};

const BRAIN_LABELS: Record<string, string> = {
  "qwen-turbo": "闪电快",
  "deepseek-chat": "聪明",
  "claude-sonnet": "超级聪明",
  "gpt-4o": "超级聪明",
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

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
      alert(e.message || "启动失败");
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
      alert(e.message || "停止失败");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("确定要删除这只龙虾吗？")) return;
    await deleteAgent(id);
    setAgents((prev) => prev.filter((a) => a.id !== id));
  }

  if (loading) return <div className="p-8 text-gray-400">加载中...</div>;

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-white mb-8">管理龙虾</h1>

      {agents.length === 0 ? (
        <p className="text-gray-500">你还没有龙虾，去首页创建一只吧</p>
      ) : (
        <div className="space-y-4">
          {agents.map((agent) => {
            const status = STATUS_MAP[agent.status] || STATUS_MAP.stopped;
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
                        大脑: {BRAIN_LABELS[agent.model_name] || agent.model_name}
                      </p>
                      <p className={`text-sm ${status.color}`}>
                        {status.label}
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
                        {isLoading ? "启动中..." : "启动"}
                      </button>
                    )}
                    {isRunning && (
                      <button
                        onClick={() => handleStop(agent.id)}
                        disabled={isLoading}
                        className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition"
                      >
                        {isLoading ? "停止中..." : "停止"}
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(agent.id)}
                      className="text-sm text-red-400 hover:text-red-300"
                    >
                      删除
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
