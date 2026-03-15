"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { apiGet, apiPost, getAgentSkills, uninstallSkill, toggleAgentSkill } from "@/lib/api";
import type { Agent, Conversation, Message, AgentSkill } from "@/lib/types";
import { useChat } from "@/hooks/use-chat";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { ChatMarkdown } from "@/components/chat-markdown";
import { cn } from "@/lib/cn";
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
      <div className="flex items-center gap-1 rounded-lg bg-accent px-4 py-3">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground"
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
        <div className="flex-1 rounded-lg border border-border bg-card p-4">
          <div className="space-y-4">
            <div className="flex justify-end"><Skeleton className="h-10 w-48" /></div>
            <div className="flex justify-start"><Skeleton className="h-16 w-64" /></div>
            <div className="flex justify-end"><Skeleton className="h-10 w-36" /></div>
            <div className="flex justify-start"><Skeleton className="h-20 w-56" /></div>
          </div>
        </div>
        <Skeleton className="mt-4 h-10 w-full" />
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
    <div className="border-t border-border pt-3 mt-3">
      <button
        onClick={() => setShowOps(!showOps)}
        className="flex w-full items-center justify-between text-sm font-semibold"
      >
        <span className="flex items-center gap-1.5">
          <Terminal className="h-3.5 w-3.5" />
          Ops Panel
        </span>
        {showOps ? (
          <ChevronUp className="h-3.5 w-3.5 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        )}
      </button>

      {showOps && (
        <div className="mt-3 space-y-3">
          {/* Quick actions */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRestart}
              disabled={restarting || agent.status === "creating"}
              className="h-7 text-xs"
            >
              <RotateCcw className={cn("mr-1 h-3 w-3", restarting && "animate-spin")} />
              {restarting ? "Restarting..." : "Restart"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchHealth}
              disabled={loadingHealth}
              className="h-7 text-xs"
            >
              <Heart className="mr-1 h-3 w-3" />
              Health
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchLogs}
              disabled={loadingLogs}
              className="h-7 text-xs"
            >
              <Terminal className="mr-1 h-3 w-3" />
              Logs
            </Button>
          </div>

          {/* Health display */}
          {health && (
            <div className="rounded-lg bg-muted/50 p-2 text-xs">
              <div className="mb-1 flex items-center gap-2">
                <span className="text-muted-foreground">Status:</span>
                <span className={cn(
                  "rounded px-1.5 py-0.5 font-medium",
                  healthStatus === "healthy"
                    ? "bg-green-500/20 text-green-400"
                    : healthStatus === "unhealthy"
                      ? "bg-red-500/20 text-red-400"
                      : "bg-yellow-500/20 text-yellow-400"
                )}>
                  {healthStatus || health.status}
                </span>
              </div>
              {health.restart_count !== undefined && (
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Restarts:</span>
                  <span>{health.restart_count}</span>
                </div>
              )}
              {health.started_at && (
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Up since:</span>
                  <span>{formatTime(health.started_at) || "—"}</span>
                </div>
              )}
            </div>
          )}

          {/* Logs display */}
          {logs !== null && (
            <div className="max-h-40 overflow-y-auto rounded-lg bg-black/50 p-2">
              <pre className="whitespace-pre-wrap text-[10px] leading-tight text-green-400/80 font-mono">
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

  const { messages, setMessages, isStreaming, error, sendMessage, cancelStream } = useChat({
    agentId,
    conversationId: activeConvId,
    onConversationCreated: (id) => {
      setActiveConvId(id);
      fetchConversations();
    },
  });

  const fetchConversations = () => {
    apiGet<Conversation[]>(`/agents/${agentId}/conversations`)
      .then(setConversations)
      .catch(() => {});
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
      <div className="flex h-64 flex-col items-center justify-center gap-3" role="alert">
        <AlertCircle className="h-8 w-8 text-destructive" />
        <p className="text-sm text-muted-foreground">{fetchError}</p>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="flex h-64 items-center justify-center" role="alert">
        <p className="text-sm text-muted-foreground">Agent not found.</p>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-5rem)] md:h-[calc(100vh-4rem)] gap-4">
      {/* Mobile sidebar toggle */}
      <button
        className="fixed bottom-20 right-4 z-20 flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg md:hidden"
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
            ? "fixed inset-y-0 left-0 z-30 flex bg-background p-4 pt-18 shadow-xl md:relative md:p-0 md:pt-0 md:shadow-none"
            : "hidden md:flex"
        )}
      >
        <Card>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h2 className="font-semibold">{agent.name}</h2>
              <p className="text-xs text-muted-foreground">
                {agent.model_name}
              </p>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2">
            <span
              className={`rounded px-2 py-0.5 text-xs ${
                agent.status === "running"
                  ? "bg-green-500/20 text-green-400"
                  : "bg-yellow-500/20 text-yellow-400"
              }`}
            >
              {agent.status}
            </span>
            {(agent.status === "running" || agent.status === "stopped") && (
              <Button
                variant="ghost"
                size="sm"
                aria-label={agent.status === "running" ? "Stop agent" : "Start agent"}
                onClick={async () => {
                  const action = agent.status === "running" ? "stop" : "start";
                  try {
                    const updated = await apiPost<Agent>(`/agents/${agentId}/${action}`);
                    setAgent(updated);
                    toast.success(`Agent ${action === "start" ? "started" : "stopped"}`);
                  } catch {
                    toast.error(`Failed to ${action} agent`);
                  }
                }}
                className={
                  agent.status === "running"
                    ? "h-7 text-yellow-400 hover:text-yellow-300"
                    : "h-7 text-green-400 hover:text-green-300"
                }
              >
                {agent.status === "running" ? (
                  <Square className="h-3 w-3" />
                ) : (
                  <Play className="h-3 w-3" />
                )}
              </Button>
            )}
          </div>
        </Card>

        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Conversations</h3>
          <Button variant="ghost" size="sm" onClick={handleNewConversation}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 space-y-1 overflow-y-auto">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => loadConversation(conv.id)}
              className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors ${
                activeConvId === conv.id
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              }`}
            >
              <MessageSquare className="h-3 w-3 shrink-0" />
              <span className="truncate">{conv.title}</span>
            </button>
          ))}
          {conversations.length === 0 && (
            <p className="px-3 text-xs text-muted-foreground">
              No conversations yet. Send a message to start.
            </p>
          )}
        </div>

        {/* Installed Skills */}
        <div className="border-t border-border pt-3 mt-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold flex items-center gap-1.5">
              <Package className="h-3.5 w-3.5" />
              Skills
            </h3>
            <Link href="/clawhub">
              <Button variant="ghost" size="sm" className="h-6 text-xs text-primary">
                Browse
              </Button>
            </Link>
          </div>
          <div className="space-y-1">
            {agentSkills.map((as) => (
              <div
                key={as.id}
                className="flex items-center justify-between rounded-md px-2 py-1.5 text-sm"
              >
                <span className={as.enabled ? "text-foreground" : "text-muted-foreground line-through"}>
                  {as.skill.name}
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={async () => {
                      try {
                        await toggleAgentSkill(agentId, as.skill.id, !as.enabled);
                        setAgentSkills((prev) =>
                          prev.map((s) =>
                            s.id === as.id ? { ...s, enabled: !s.enabled } : s
                          )
                        );
                        toast.success(`Skill ${as.enabled ? "disabled" : "enabled"}`);
                      } catch {
                        toast.error("Failed to toggle skill");
                      }
                    }}
                    className="rounded p-0.5 text-muted-foreground hover:text-foreground"
                    title={as.enabled ? "Disable" : "Enable"}
                    aria-label={as.enabled ? `Disable ${as.skill.name}` : `Enable ${as.skill.name}`}
                  >
                    {as.enabled ? (
                      <ToggleRight className="h-4 w-4 text-green-400" />
                    ) : (
                      <ToggleLeft className="h-4 w-4" />
                    )}
                  </button>
                  <button
                    onClick={() => setUninstallTarget(as)}
                    className="rounded p-0.5 text-muted-foreground hover:text-red-400"
                    title="Uninstall"
                    aria-label={`Uninstall ${as.skill.name}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            ))}
            {agentSkills.length === 0 && (
              <p className="px-2 text-xs text-muted-foreground">
                No skills installed.{" "}
                <Link href="/clawhub" className="text-primary hover:underline">
                  Browse ClawHub
                </Link>
              </p>
            )}
          </div>
        </div>

        {/* Ops Panel — inspired by 秋芝 Qclaw */}
        <AgentOpsPanel agentId={agentId} agent={agent} setAgent={setAgent} />
      </div>

      {/* Overlay for mobile sidebar */}
      {showSidebar && (
        <div
          className="fixed inset-0 z-20 bg-black/50 md:hidden"
          onClick={() => setShowSidebar(false)}
        />
      )}

      {/* Right: chat area */}
      <div className="flex flex-1 flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto rounded-lg border border-border bg-card p-4">
          {messages.length === 0 && !isStreaming ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <Bot className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                <p className="text-muted-foreground">
                  Send a message to start chatting with {agent.name}.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[90%] md:max-w-[75%] rounded-lg px-4 py-2 text-sm ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-accent text-accent-foreground"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <ChatMarkdown content={msg.content} />
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                    {msg.timestamp && (
                      <p className={`mt-1 text-[10px] ${
                        msg.role === "user"
                          ? "text-primary-foreground/50"
                          : "text-muted-foreground/60"
                      }`}>
                        {formatTime(msg.timestamp)}
                      </p>
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

        {/* Error */}
        {error && (
          <div className="mt-2 flex items-center gap-2 text-sm text-destructive" role="alert" aria-live="polite">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Input */}
        <form onSubmit={handleSend} className="mt-4 flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            disabled={isStreaming}
            className="flex-1"
          />
          {isStreaming ? (
            <Button
              type="button"
              variant="outline"
              onClick={cancelStream}
              aria-label="Stop generating"
              title="Stop generating"
              className="border-red-500/50 text-red-400 hover:bg-red-500/10 hover:text-red-300"
            >
              <StopCircle className="h-4 w-4" />
            </Button>
          ) : (
            <Button type="submit" disabled={!input.trim()} aria-label="Send message">
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
