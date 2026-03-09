"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useToolCatalog } from "@/hooks/useToolStore";
import { useAgents } from "@/hooks/useAgent";
import { installTool } from "@/lib/api";
import type { ToolInfo } from "@/lib/api";

const ICON_MAP: Record<string, string> = {
  folder: "📁", globe: "🌐", search: "🔍", github: "🐙", database: "🗄️",
  brain: "🧠", terminal: "💻", image: "🖼️", languages: "🌍", text: "📝",
  shield: "🛡️", pencil: "✏️", chart: "📊", server: "🖥️", book: "📖",
  code: "💻", zap: "⚡",
};

const TYPE_COLORS: Record<string, string> = {
  mcp: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  skill: "bg-green-500/10 text-green-400 border-green-500/20",
  prompt: "bg-purple-500/10 text-purple-400 border-purple-500/20",
};

export default function ToolStorePage() {
  const t = useTranslations("toolstore");
  const { tools, categories, loading, category, setCategory, search, setSearch } = useToolCatalog();
  const { agents } = useAgents();
  const [installing, setInstalling] = useState<string | null>(null);
  const [agentPicker, setAgentPicker] = useState<ToolInfo | null>(null);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  async function handleInstall(tool: ToolInfo, agentId: string) {
    setAgentPicker(null);
    setInstalling(tool.id);
    try {
      const result = await installTool(agentId, tool.id);
      if (result.status === "already_installed") {
        setMessage({ text: t("alreadyInstalled"), type: "error" });
      } else {
        setMessage({
          text: result.needs_restart ? t("installSuccess") : t("installSuccessNoRestart"),
          type: "success",
        });
      }
    } catch (e: unknown) {
      setMessage({ text: e instanceof Error ? e.message : "Install failed", type: "error" });
    } finally {
      setInstalling(null);
      setTimeout(() => setMessage(null), 4000);
    }
  }

  if (loading) {
    return (
      <div className="p-10 max-w-5xl">
        <div className="h-7 w-32 bg-surface-hover rounded animate-pulse mb-8" />
        <div className="flex gap-2 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-8 w-20 bg-surface-hover rounded-full animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="border border-border rounded-lg p-4 animate-pulse">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 bg-surface-hover rounded" />
                <div className="h-4 w-24 bg-surface-hover rounded" />
              </div>
              <div className="h-3 w-full bg-surface-hover rounded mb-2" />
              <div className="h-3 w-2/3 bg-surface-hover rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-10 max-w-5xl">
      <h1 className="text-xl font-semibold text-foreground tracking-tight mb-6">{t("title")}</h1>

      {/* Notification */}
      {message && (
        <div
          className={`mb-4 px-4 py-2.5 rounded-lg border text-xs flex items-center justify-between ${
            message.type === "success"
              ? "bg-green-500/10 border-green-500/20 text-green-400"
              : "bg-red-500/10 border-red-500/20 text-red-400"
          }`}
        >
          <span>{message.text}</span>
          <button onClick={() => setMessage(null)} className="ml-4 hover:opacity-70">×</button>
        </div>
      )}

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t("searchPlaceholder")}
          className="w-full max-w-sm px-3 py-2 text-sm bg-surface border border-border rounded-lg text-foreground placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>

      {/* Category filters */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => setCategory(null)}
          className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
            category === null
              ? "bg-accent text-white border-accent"
              : "border-border text-muted hover:text-foreground hover:bg-surface"
          }`}
        >
          {t("allCategories")}
        </button>
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setCategory(cat.id)}
            className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
              category === cat.id
                ? "bg-accent text-white border-accent"
                : "border-border text-muted hover:text-foreground hover:bg-surface"
            }`}
          >
            {ICON_MAP[cat.icon] || ""} {cat.name}
          </button>
        ))}
      </div>

      {/* Tool grid */}
      {tools.length === 0 ? (
        <p className="text-sm text-muted">{t("noResults")}</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {tools
            .sort((a, b) => b.popularity - a.popularity)
            .map((tool) => (
              <div
                key={tool.id}
                className="border border-border rounded-lg p-4 hover:border-accent/30 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl">{ICON_MAP[tool.icon] || "🔧"}</span>
                    <div>
                      <h3 className="text-sm font-medium text-foreground">{tool.name}</h3>
                      <span
                        className={`inline-block mt-0.5 px-1.5 py-0.5 text-[10px] font-medium rounded border ${
                          TYPE_COLORS[tool.type] || ""
                        }`}
                      >
                        {t(`type${tool.type.charAt(0).toUpperCase() + tool.type.slice(1)}` as "typeMcp" | "typeSkill" | "typePrompt")}
                      </span>
                    </div>
                  </div>
                </div>

                <p className="text-xs text-muted leading-relaxed mb-3">{tool.description}</p>

                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-muted">{tool.author}</span>
                  <button
                    onClick={() => setAgentPicker(tool)}
                    disabled={installing === tool.id}
                    className="px-2.5 py-1 text-xs font-medium text-accent border border-accent/30 rounded-md hover:bg-accent/10 disabled:opacity-40 transition-colors"
                  >
                    {installing === tool.id ? (
                      <span className="inline-flex items-center gap-1">
                        <span className="inline-block w-3 h-3 border border-current/30 border-t-current rounded-full animate-spin" />
                      </span>
                    ) : (
                      t("addToAgent")
                    )}
                  </button>
                </div>
              </div>
            ))}
        </div>
      )}

      {/* Agent picker modal */}
      {agentPicker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-background border border-border rounded-xl p-6 w-full max-w-sm shadow-xl">
            <h3 className="text-sm font-semibold text-foreground mb-1">{t("selectAgent")}</h3>
            <p className="text-xs text-muted mb-4">
              {agentPicker.name}
            </p>

            {agents.length === 0 ? (
              <p className="text-xs text-muted py-4">{t("noAgents")}</p>
            ) : (
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => handleInstall(agentPicker, agent.id)}
                    className="w-full text-left px-3 py-2.5 text-sm text-foreground border border-border rounded-lg hover:bg-surface hover:border-accent/30 transition-colors"
                  >
                    {agent.name}
                    <span className="text-xs text-muted ml-2">({agent.model_name})</span>
                  </button>
                ))}
              </div>
            )}

            <button
              onClick={() => setAgentPicker(null)}
              className="mt-4 w-full px-3 py-2 text-xs text-muted border border-border rounded-lg hover:text-foreground hover:bg-surface transition-colors"
            >
              {t("cancel")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
