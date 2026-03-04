"use client";

import { useEffect, useState } from "react";
import { listAgents, deleteAgent, type Agent } from "@/lib/api";

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  running: { label: "🟢 在线", color: "text-green-400" },
  stopped: { label: "😴 休息中", color: "text-gray-400" },
  creating: { label: "⏳ 创建中", color: "text-yellow-400" },
  error: { label: "🤒 不舒服", color: "text-red-400" },
};

const BRAIN_LABELS: Record<string, string> = {
  "qwen-turbo": "⚡ 闪电快",
  "deepseek-chat": "🧠 聪明",
  "claude-sonnet": "🎓 超级聪明",
  "gpt-4o": "🎓 超级聪明",
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listAgents()
      .then(setAgents)
      .finally(() => setLoading(false));
  }, []);

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
            return (
              <div
                key={agent.id}
                className="bg-gray-900 border border-gray-800 rounded-xl p-6"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="text-3xl">🦞</div>
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
                  <button
                    onClick={() => handleDelete(agent.id)}
                    className="text-sm text-red-400 hover:text-red-300"
                  >
                    删除
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
