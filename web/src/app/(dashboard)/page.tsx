"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { listAgents, createAgent, type Agent } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  running: { label: "🟢 在线", color: "text-green-400" },
  stopped: { label: "😴 休息中", color: "text-gray-400" },
  creating: { label: "⏳ 创建中", color: "text-yellow-400" },
  error: { label: "🤒 不舒服", color: "text-red-400" },
};

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    listAgents()
      .then(setAgents)
      .finally(() => setLoading(false));
  }, []);

  async function handleCreateAgent() {
    setCreating(true);
    try {
      const agent = await createAgent("我的龙虾", "deepseek-chat");
      setAgents((prev) => [agent, ...prev]);
    } catch {
      // ignore
    } finally {
      setCreating(false);
    }
  }

  if (loading) {
    return (
      <div className="p-8 text-gray-400">加载中...</div>
    );
  }

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">
            你好，{user?.name} 👋
          </h1>
          <p className="text-gray-500 mt-1">⚡ {user?.credit_balance} 能量可用</p>
        </div>
        {agents.length === 0 && (
          <button
            onClick={handleCreateAgent}
            disabled={creating}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-xl transition"
          >
            {creating ? "正在孵化..." : "🦞 创建我的龙虾"}
          </button>
        )}
      </div>

      {agents.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-6xl mb-4">🦞</div>
          <h2 className="text-xl font-semibold text-white mb-2">
            你还没有龙虾
          </h2>
          <p className="text-gray-500 mb-6">
            创建一只龙虾，它会 24/7 陪你聊天、帮你做事
          </p>
          <button
            onClick={handleCreateAgent}
            disabled={creating}
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white text-lg font-semibold rounded-xl transition"
          >
            {creating ? "🥚 龙虾正在孵化..." : "🦞 创建我的第一只龙虾"}
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {agents.map((agent) => {
            const status = STATUS_MAP[agent.status] || STATUS_MAP.stopped;
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
                        大脑: {agent.model_name}
                      </p>
                    </div>
                  </div>
                  <div className={`text-sm font-medium ${status.color}`}>
                    {status.label}
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
