"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { apiGet, apiPost, getAgentSkills, uninstallSkill, toggleAgentSkill } from "@/lib/api";
import type { Agent, Conversation, Message, AgentSkill } from "@/lib/types";
import { useChat } from "@/hooks/use-chat";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { ChatMarkdown } from "@/components/chat-markdown";
import { cn } from "@/lib/cn";
import { useLanguage } from "@/context/language-context";
import Link from "next/link";
import { toast } from "sonner";
import {
  Bot,
  Send,
  Plus,
  MessageSquare,
  Play,
  Square,
  PanelLeftOpen,
  PanelLeftClose,
  Package,
  Trash2,
  ToggleLeft,
  ToggleRight,
  AlertCircle,
  RefreshCw,
  RotateCcw,
  Heart,
  Terminal,
  StopCircle,
  ChevronDown,
  ChevronUp,
  Download,
} from "lucide-react";

function formatTime(iso?: string) {
  if (!iso) return null;
  const d = new Date(iso);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  return sameDay
    ? d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : `${d.getMonth() + 1}/${d.getDate()} ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-1 rounded-2xl bg-[#f7f7f7] dark:bg-[#262626] px-4 py-3 border border-[#ebebeb] dark:border-[#333]">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="inline-block h-1.5 w-1.5 rounded-full bg-[#b0b0b0] dark:bg-[#666]"
            style={{
              animation: "typing-dot 1.2s infinite",
              animationDelay: `${i * 150}ms`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

function Skeleton({ className }: { className?: string }) {
  return <div className={`skeleton-shimmer rounded-2xl ${className ?? ""}`} />;
}

function ChatSkeleton() {
  return (
    <div className="flex h-[calc(100vh-5rem)] md:h-[calc(100vh-4rem)] gap-4">
      <div className="hidden w-64 shrink-0 flex-col gap-4 md:flex">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-6 w-32" />
        <div className="space-y-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-3/4" />
        </div>
      </div>
      <div className="flex flex-1 flex-col">
        <div className="flex-1 rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-4">
          <div className="space-y-4">
            <div className="flex justify-end"><Skeleton className="h-10 w-48" /></div>
            <div className="flex justify-start"><Skeleton className="h-16 w-64" /></div>
            <div className="flex justify-end"><Skeleton className="h-10 w-36" /></div>
            <div className="flex justify-start"><Skeleton className="h-20 w-56" /></div>
          </div>
        </div>
        <Skeleton className="mt-4 h-11 w-full" />
      </div>
    </div>
  );
}

// --- Agent Ops Panel ---
function AgentOpsPanel({ agentId, agent, setAgent }: {
  agentId: string;
  agent: Agent;
  setAgent: (a: Agent) => void;
}) {
  const [showOps, setShowOps] = useState(false);
  const [health, setHealth] = useState<{
    status?: string;
    running?: boolean;
    started_at?: string;
    health_status?: string;
    restart_count?: number;
  } | null>(null);
  const [logs, setLogs] = useState<string | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [restarting, setRestarting] = useState(false);

  const fetchHealth = async () => {
    setLoadingHealth(true);
    try {
      const h = await apiGet<typeof health>(`/agents/${agentId}/health`);
      setHealth(h);
    } catch {
      toast.error("Failed to fetch health");
    } finally {
      setLoadingHealth(false);
    }
  };

  const fetchLogs = async () => {
    setLoadingLogs(true);
    try {
      const res = await apiGet<{ logs: string }>(`/agents/${agentId}/logs`);
      setLogs(res.logs);
    } catch {
      toast.error("Failed to fetch logs");
    } finally {
      setLoadingLogs(false);
    }
  };

  const handleRestart = async () => {
    setRestarting(true);
    try {
      const updated = await apiPost<Agent>(`/agents/${agentId}/restart`);
      setAgent(updated);
      toast.success("Agent restarted");
    } catch {
      toast.error("Failed to restart agent");
    } finally {
      setRestarting(false);
    }
  };

  const healthStatus = health?.health_status;

  return (
    <div className="border-t border-[#ebebeb] dark:border-[#333] pt-3 mt-3">
      <button
        onClick={() => setShowOps(!showOps)}
        className="flex w-full items-center justify-between text-sm font-bold text-[#222222] dark:text-white"
      >
        <span className="flex items-center gap-1.5">
          <Terminal className="h-3.5 w-3.5 text-[#717171] dark:text-[#a0a0a0]" />
          Ops Panel
        </span>
        {showOps ? (
          <ChevronUp className="h-3.5 w-3.5 text-[#b0b0b0] dark:text-[#666]" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 text-[#b0b0b0] dark:text-[#666]" />
        )}
      </button>

      {showOps && (
        <div className="mt-3 space-y-3">
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={handleRestart} disabled={restarting || agent.status === "creating"}
              className="h-7 text-xs border-[#dddddd] dark:border-[#444] text-[#222222] dark:text-white hover:bg-[#f7f7f7] dark:hover:bg-[#262626] rounded-lg">
              <RotateCcw className={cn("mr-1 h-3 w-3", restarting && "animate-spin")} />
              {restarting ? "Restarting..." : "Restart"}
            </Button>
            <Button variant="outline" size="sm" onClick={fetchHealth} disabled={loadingHealth}
              className="h-7 text-xs border-[#dddddd] dark:border-[#444] text-[#222222] dark:text-white hover:bg-[#f7f7f7] dark:hover:bg-[#262626] rounded-lg">
              <Heart className="mr-1 h-3 w-3" />
              Health
            </Button>
            <Button variant="outline" size="sm" onClick={fetchLogs} disabled={loadingLogs}
              className="h-7 text-xs border-[#dddddd] dark:border-[#444] text-[#222222] dark:text-white hover:bg-[#f7f7f7] dark:hover:bg-[#262626] rounded-lg">
              <Terminal className="mr-1 h-3 w-3" />
              Logs
            </Button>
          </div>

          {health && (
            <div className="rounded-xl bg-[#f7f7f7] dark:bg-[#262626] border border-[#ebebeb] dark:border-[#333] p-3 text-xs">
              <div className="mb-1 flex items-center gap-2">
                <span className="text-[#717171] dark:text-[#a0a0a0]">Status:</span>
                <span className={cn(
                  "rounded-full px-2 py-0.5 font-semibold",
                  healthStatus === "healthy"
                    ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400"
                    : healthStatus === "unhealthy"
                      ? "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
                      : "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400"
                )}>
                  {healthStatus || health.status}
                </span>
              </div>
              {health.restart_count !== undefined && (
                <div className="flex items-center gap-2 text-[#717171] dark:text-[#a0a0a0]">
                  <span>Restarts:</span><span className="text-[#222222] dark:text-white">{health.restart_count}</span>
                </div>
              )}
              {health.started_at && (
                <div className="flex items-center gap-2 text-[#717171] dark:text-[#a0a0a0]">
                  <span>Up since:</span><span className="text-[#222222] dark:text-white">{formatTime(health.started_at) || "—"}</span>
                </div>
              )}
            </div>
          )}

          {logs !== null && (
            <div className="max-h-40 overflow-y-auto rounded-xl bg-[#1a1a1a] dark:bg-[#0d0d0d] p-3">
              <pre className="whitespace-pre-wrap text-[10px] leading-tight text-emerald-400 font-mono">
                {logs || "(no logs)"}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AgentDetailPage() {
  const params = useParams();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [agentSkills, setAgentSkills] = useState<AgentSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [showSidebar, setShowSidebar] = useState(false);
  const [uninstallTarget, setUninstallTarget] = useState<AgentSkill | null>(null);
  const [uninstalling, setUninstalling] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { t } = useLanguage();
  const { messages, setMessages, isStreaming, error, sendMessage, cancelStream, connectionStatus } = useChat({
    agentId,
    conversationId: activeConvId,
    onConversationCreated: (id) => {
      setActiveConvId(id);
      fetchConversations();
    },
  });

  const handleToggleAgent = useCallback(async () => {
    if (!agent) return;
    const action = agent.status === "running" ? "stop" : "start";
    try {
      const updated = await apiPost<Agent>(`/agents/${agentId}/${action}`);
      setAgent(updated);
      toast.success(`Agent ${action === "start" ? "started" : "stopped"}`);
    } catch {
      toast.error(`Failed to ${action} agent`);
    }
  }, [agent, agentId]);

  const fetchConversations = () => {
    apiGet<Conversation[]>(`/agents/${agentId}/conversations`)
      .then(setConversations)
      .catch(() => toast.error("Failed to load conversations"));
  };

  const fetchData = () => {
    setLoading(true);
    setFetchError(null);
    Promise.all([
      apiGet<Agent>(`/agents/${agentId}`),
      apiGet<Conversation[]>(`/agents/${agentId}/conversations`),
      getAgentSkills(agentId),
    ])
      .then(([a, c, s]) => {
        setAgent(a);
        setConversations(c);
        setAgentSkills(s);
      })
      .catch((err) => setFetchError(err.message || "Failed to load agent"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, [agentId]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const loadConversation = async (convId: string) => {
    setActiveConvId(convId);
    setShowSidebar(false);
    try {
      const history = await apiGet<Message[]>(
        `/conversations/${convId}/messages`,
      );
      setMessages(
        history.map((m) => ({
          role: m.role as "user" | "assistant",
          content: m.content,
          timestamp: m.created_at,
          usage: m.credits_used != null ? {
            credits_used: m.credits_used,
            tokens_input: m.tokens_input ?? 0,
            tokens_output: m.tokens_output ?? 0,
            model: m.model_name ?? "",
            balance: 0,
          } : undefined,
        })),
      );
    } catch {
      toast.error("Failed to load conversation");
    }
  };

  const handleNewConversation = () => {
    setActiveConvId(null);
    setMessages([]);
    setShowSidebar(false);
  };

  const handleExport = async (format: "md" | "json" | "txt") => {
    if (!activeConvId) {
      toast.error("No conversation to export");
      return;
    }
    try {
      const token = localStorage.getItem("clawzy_access_token");
      const res = await fetch(`/api/v1/conversations/${activeConvId}/export?format=${format}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `conversation.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Exported!");
    } catch {
      toast.error("Failed to export conversation");
    }
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input.trim());
    setInput("");
  };

  const handleUninstallSkill = async () => {
    if (!uninstallTarget) return;
    setUninstalling(true);
    try {
      await uninstallSkill(agentId, uninstallTarget.skill.id);
      setAgentSkills((prev) => prev.filter((s) => s.id !== uninstallTarget.id));
      toast.success(`${uninstallTarget.skill.name} uninstalled`);
    } catch {
      toast.error("Failed to uninstall skill");
    } finally {
      setUninstalling(false);
      setUninstallTarget(null);
    }
  };

  if (loading) return <ChatSkeleton />;

  if (fetchError) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a]" role="alert">
        <AlertCircle className="h-8 w-8 text-[#ff385c]" />
        <p className="text-sm text-[#717171] dark:text-[#a0a0a0]">{fetchError}</p>
        <Button variant="outline" size="sm" onClick={fetchData} className="border-[#dddddd] dark:border-[#444]">
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="flex h-64 items-center justify-center rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a]" role="alert">
        <p className="text-sm text-[#717171] dark:text-[#a0a0a0]">Agent not found.</p>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-5rem)] md:h-[calc(100vh-4rem)] gap-4">
      {/* Mobile sidebar toggle */}
      <button
        className="fixed bottom-20 right-4 z-20 flex h-10 w-10 items-center justify-center rounded-full bg-[#ff385c] text-white shadow-lg md:hidden"
        onClick={() => setShowSidebar(!showSidebar)}
        aria-label={showSidebar ? "Close sidebar" : "Open sidebar"}
        aria-expanded={showSidebar}
      >
        {showSidebar ? (
          <PanelLeftClose className="h-5 w-5" />
        ) : (
          <PanelLeftOpen className="h-5 w-5" />
        )}
      </button>

      {/* Left sidebar: agent info + conversations */}
      <div
        className={cn(
          "w-64 shrink-0 flex-col gap-4 overflow-y-auto",
          showSidebar
            ? "fixed inset-y-0 left-0 z-30 flex bg-white dark:bg-[#1a1a1a] p-4 pt-18 shadow-xl md:relative md:p-0 md:pt-0 md:shadow-none"
            : "hidden md:flex"
        )}
      >
        {/* Agent info card */}
        <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-4 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl icon-gradient-red shadow-sm">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-[#222222] dark:text-white">{agent.name}</h2>
              <p className="text-xs text-[#717171] dark:text-[#a0a0a0]">{agent.model_name}</p>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2">
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                agent.status === "running"
                  ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400"
                  : "bg-[#f7f7f7] dark:bg-[#262626] text-[#717171] dark:text-[#a0a0a0]"
              }`}
            >
              {agent.status}
            </span>
            {(agent.status === "running" || agent.status === "stopped") && (
              <Button
                variant="ghost"
                size="sm"
                aria-label={agent.status === "running" ? "Stop agent" : "Start agent"}
                onClick={handleToggleAgent}
                className={cn(
                  "h-7 rounded-lg",
                  agent.status === "running"
                    ? "text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20"
                    : "text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
                )}
              >
                {agent.status === "running" ? (
                  <Square className="h-3 w-3" />
                ) : (
                  <Play className="h-3 w-3" />
                )}
              </Button>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between px-1">
          <h3 className="text-sm font-bold text-[#222222] dark:text-white">Conversations</h3>
          <div className="flex items-center gap-1">
            {activeConvId && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleExport("md")}
                title="Export conversation"
                className="rounded-lg text-[#717171] dark:text-[#a0a0a0] hover:bg-[#f7f7f7] dark:hover:bg-[#262626]"
              >
                <Download className="h-4 w-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleNewConversation}
              className="rounded-lg text-[#717171] dark:text-[#a0a0a0] hover:bg-[#f7f7f7] dark:hover:bg-[#262626]"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex-1 space-y-0.5 overflow-y-auto">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => loadConversation(conv.id)}
              className={`flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm transition-colors ${
                activeConvId === conv.id
                  ? "bg-[#fff0f2] dark:bg-[#ff385c]/10 text-[#ff385c]"
                  : "text-[#717171] dark:text-[#a0a0a0] hover:bg-[#f7f7f7] dark:hover:bg-[#262626] hover:text-[#222222] dark:hover:text-white"
              }`}
            >
              <MessageSquare className="h-3 w-3 shrink-0" />
              <span className="truncate">{conv.title}</span>
            </button>
          ))}
          {conversations.length === 0 && (
            <p className="px-3 text-xs text-[#b0b0b0] dark:text-[#666]">
              No conversations yet. Send a message to start.
            </p>
          )}
        </div>

        {/* Installed Skills */}
        <div className="border-t border-[#ebebeb] dark:border-[#333] pt-3 mt-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-bold text-[#222222] dark:text-white flex items-center gap-1.5">
              <Package className="h-3.5 w-3.5" />
              Skills
            </h3>
            <Link href="/clawhub">
              <Button variant="ghost" size="sm" className="h-6 text-xs text-[#ff385c] hover:bg-[#fff0f2] dark:hover:bg-[#ff385c]/10">
                Browse
              </Button>
            </Link>
          </div>
          <div className="space-y-0.5">
            {agentSkills.map((as) => (
              <div
                key={as.id}
                className="flex items-center justify-between rounded-xl px-2 py-1.5 text-sm hover:bg-[#f7f7f7] dark:hover:bg-[#262626]"
              >
                <span className={as.enabled ? "text-[#222222] dark:text-white" : "text-[#b0b0b0] dark:text-[#666] line-through"}>
                  {as.skill.name}
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={async () => {
                      const newEnabled = !as.enabled;
                      try {
                        await toggleAgentSkill(agentId, as.skill.id, newEnabled);
                        setAgentSkills((prev) =>
                          prev.map((s) =>
                            s.id === as.id ? { ...s, enabled: newEnabled } : s
                          )
                        );
                        toast.success(`Skill ${newEnabled ? "enabled" : "disabled"}`);
                      } catch {
                        toast.error("Failed to toggle skill");
                      }
                    }}
                    className="rounded p-0.5 text-[#b0b0b0] dark:text-[#666] hover:text-[#222222] dark:hover:text-white"
                    title={as.enabled ? "Disable" : "Enable"}
                    aria-label={as.enabled ? `Disable ${as.skill.name}` : `Enable ${as.skill.name}`}
                  >
                    {as.enabled ? (
                      <ToggleRight className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <ToggleLeft className="h-4 w-4" />
                    )}
                  </button>
                  <button
                    onClick={() => setUninstallTarget(as)}
                    className="rounded p-0.5 text-[#b0b0b0] dark:text-[#666] hover:text-[#ff385c]"
                    title="Uninstall"
                    aria-label={`Uninstall ${as.skill.name}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            ))}
            {agentSkills.length === 0 && (
              <p className="px-2 text-xs text-[#b0b0b0] dark:text-[#666]">
                No skills installed.{" "}
                <Link href="/clawhub" className="text-[#ff385c] hover:underline">
                  Browse ClawHub
                </Link>
              </p>
            )}
          </div>
        </div>

        {/* Ops Panel */}
        <AgentOpsPanel agentId={agentId} agent={agent} setAgent={setAgent} />
      </div>

      {/* Overlay for mobile sidebar */}
      {showSidebar && (
        <div
          className="fixed inset-0 z-20 bg-black/30 backdrop-blur-sm md:hidden"
          onClick={() => setShowSidebar(false)}
        />
      )}

      {/* Right: chat area */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-4 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
          {messages.length === 0 && !isStreaming ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl icon-gradient-red shadow-md">
                  <Bot className="h-8 w-8 text-white" />
                </div>
                <p className="font-semibold text-[#222222] dark:text-white">{agent.name}</p>
                <p className="mt-1 text-sm text-[#717171] dark:text-[#a0a0a0]">
                  Send a message to start chatting.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[90%] md:max-w-[75%] rounded-2xl px-4 py-3 text-sm ${
                      msg.role === "user"
                        ? "bg-[#ff385c] text-white shadow-[0_2px_8px_rgba(255,56,92,0.25)]"
                        : "bg-[#f7f7f7] dark:bg-[#262626] text-[#222222] dark:text-white border border-[#ebebeb] dark:border-[#333]"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <ChatMarkdown content={msg.content} />
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                    {(msg.timestamp || msg.usage) && (
                      <div className={`mt-1.5 flex items-center gap-2 text-[10px] ${
                        msg.role === "user" ? "text-white/60" : "text-[#b0b0b0] dark:text-[#666]"
                      }`}>
                        {msg.timestamp && <span>{formatTime(msg.timestamp)}</span>}
                        {msg.usage && (
                          <>
                            <span title={`Input: ${msg.usage.tokens_input} / Output: ${msg.usage.tokens_output} tokens`}>
                              {msg.usage.credits_used} cr
                            </span>
                            {msg.usage.routed && (
                              <span className="text-emerald-500" title="Smart routed to cheaper model">
                                {msg.usage.model}
                              </span>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isStreaming && messages[messages.length - 1]?.role !== "assistant" && (
                <TypingIndicator />
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Connection status banner */}
        {connectionStatus !== "connected" && (
          <div
            className={cn(
              "mt-2 flex items-center gap-2 rounded-xl px-3 py-2 text-sm",
              connectionStatus === "reconnecting"
                ? "bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400"
                : "bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400",
            )}
            role="status"
            aria-live="polite"
          >
            {connectionStatus === "reconnecting" ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 shrink-0 animate-spin" />
                <span>{t.chat.reconnecting}</span>
              </>
            ) : (
              <>
                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                <span>{t.chat.connectionLost}</span>
              </>
            )}
          </div>
        )}

        {/* Error */}
        {error && connectionStatus === "connected" && (
          <div className="mt-2 flex items-center gap-2 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-3 py-2 text-sm text-red-600 dark:text-red-400" role="alert" aria-live="polite">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Input */}
        <form onSubmit={handleSend} className="mt-3 flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Message ${agent.name}...`}
            disabled={isStreaming || connectionStatus !== "connected"}
            className="flex-1"
          />
          {isStreaming ? (
            <Button
              type="button"
              variant="outline"
              onClick={cancelStream}
              aria-label="Stop generating"
              title="Stop generating"
              className="border-[#dddddd] dark:border-[#444] text-[#ff385c] hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              <StopCircle className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              type="submit"
              disabled={!input.trim() || connectionStatus !== "connected"}
              aria-label="Send message"
              className="bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl shadow-sm"
            >
              <Send className="h-4 w-4" />
            </Button>
          )}
        </form>
      </div>

      {/* Uninstall confirmation */}
      <ConfirmDialog
        open={!!uninstallTarget}
        title="Uninstall Skill"
        message={`Are you sure you want to uninstall "${uninstallTarget?.skill.name}"? This action cannot be undone.`}
        confirmLabel="Uninstall"
        variant="danger"
        loading={uninstalling}
        onConfirm={handleUninstallSkill}
        onCancel={() => setUninstallTarget(null)}
      />
    </div>
  );
}
