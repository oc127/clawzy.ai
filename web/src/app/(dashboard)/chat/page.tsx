"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiGet, getLucyState } from "@/lib/api";
import type { Conversation, Message, LucyState } from "@/lib/types";
import { useChat } from "@/hooks/use-chat";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatMarkdown } from "@/components/chat-markdown";
import { ArtifactsPanel, type Artifact } from "@/components/artifacts-panel";
import { cn } from "@/lib/cn";
import { useLanguage } from "@/context/language-context";
import { toast } from "sonner";
import {
  Send,
  Plus,
  MessageSquare,
  PanelLeftOpen,
  PanelLeftClose,
  AlertCircle,
  RefreshCw,
  Heart,
  StopCircle,
  Download,
  FileText,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/*  Mood emoji mapping                                                 */
/* ------------------------------------------------------------------ */

const MOOD_EMOJI: Record<string, string> = {
  happy: "\u{1F60A}",
  curious: "\u{1F914}",
  excited: "\u{1F929}",
  calm: "\u{1F60C}",
  playful: "\u{1F63C}",
  focused: "\u{1F9D0}",
  loving: "\u{1F970}",
  neutral: "\u{1F642}",
};

function moodEmoji(mood: string): string {
  return MOOD_EMOJI[mood.toLowerCase()] ?? "\u{1F642}";
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

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

/* ------------------------------------------------------------------ */
/*  Lucy status badge                                                  */
/* ------------------------------------------------------------------ */

function LucyStatusBadge({ lucy }: { lucy: LucyState }) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs text-[#717171] dark:text-[#a0a0a0]">
      <span
        className="rounded-full bg-[#f7f7f7] dark:bg-[#262626] border border-[#ebebeb] dark:border-[#333] px-2.5 py-0.5"
        title={`Mood: ${lucy.mood}`}
      >
        {moodEmoji(lucy.mood)} {lucy.mood}
      </span>
      <span
        className="rounded-full bg-[#fff0f2] dark:bg-[#ff385c]/10 border border-[#ffd6dd] dark:border-[#ff385c]/20 px-2.5 py-0.5 text-[#ff385c]"
        title={`Affection: ${lucy.affection}%`}
      >
        <Heart className="mr-0.5 inline h-3 w-3" />
        {lucy.affection}
      </span>
      <span
        className="rounded-full bg-[#f7f7f7] dark:bg-[#262626] border border-[#ebebeb] dark:border-[#333] px-2.5 py-0.5"
        title={`Relationship: ${lucy.relationship_stage}`}
      >
        {lucy.relationship_stage}
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function LucyChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [lucyState, setLucyState] = useState<LucyState | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [showSidebar, setShowSidebar] = useState(false);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [showArtifacts, setShowArtifacts] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { t } = useLanguage();
  const { messages, setMessages, isStreaming, error, sendMessage, cancelStream, connectionStatus } = useChat({
    conversationId: activeConvId,
    onConversationCreated: (id) => {
      setActiveConvId(id);
      fetchConversations();
    },
  });

  const fetchConversations = () => {
    apiGet<Conversation[]>("/lucy/conversations")
      .then(setConversations)
      .catch(() => toast.error("Failed to load conversations"));
  };

  const fetchData = useCallback(() => {
    setLoading(true);
    setFetchError(null);
    Promise.all([
      apiGet<Conversation[]>("/lucy/conversations"),
      getLucyState(),
    ])
      .then(([c, ls]) => {
        setConversations(c);
        setLucyState(ls);
      })
      .catch((err) => setFetchError(err.message || "Failed to load data"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Extract artifacts (code blocks) from assistant messages
  useEffect(() => {
    const extracted: Artifact[] = [];
    const codeBlockRe = /```(\w+)?\n([\s\S]*?)```/g;
    for (const msg of messages) {
      if (msg.role !== "assistant") continue;
      let match;
      while ((match = codeBlockRe.exec(msg.content)) !== null) {
        const lang = match[1] || "text";
        const code = match[2].trimEnd();
        const id = `${lang}-${extracted.length}`;
        extracted.push({
          id,
          name: `snippet-${extracted.length + 1}.${lang === "text" ? "txt" : lang}`,
          type: "code",
          content: code,
          language: lang,
        });
      }
    }
    setArtifacts(extracted);
  }, [messages]);

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
      const token = localStorage.getItem("lucy_access_token");
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

      {/* Left sidebar: Lucy info + conversations */}
      <div
        className={cn(
          "w-64 shrink-0 flex-col gap-4 overflow-y-auto",
          showSidebar
            ? "fixed inset-y-0 left-0 z-30 flex bg-white dark:bg-[#1a1a1a] p-4 pt-18 shadow-xl md:relative md:p-0 md:pt-0 md:shadow-none"
            : "hidden md:flex"
        )}
      >
        {/* Lucy info card */}
        <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-4 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl icon-gradient-red shadow-sm">
              <Heart className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-[#222222] dark:text-white">Lucy</h2>
              <p className="text-xs text-[#717171] dark:text-[#a0a0a0]">Your AI companion</p>
            </div>
          </div>
          {lucyState && (
            <div className="mt-3">
              <LucyStatusBadge lucy={lucyState} />
            </div>
          )}
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
      </div>

      {/* Overlay for mobile sidebar */}
      {showSidebar && (
        <div
          className="fixed inset-0 z-20 bg-black/30 backdrop-blur-sm md:hidden"
          onClick={() => setShowSidebar(false)}
        />
      )}

      {/* Right: chat area + artifacts */}
      <div className="flex flex-1 gap-4 min-w-0">
      <div className="flex flex-1 flex-col min-w-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-4 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
          {messages.length === 0 && !isStreaming ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl icon-gradient-red shadow-md">
                  <Heart className="h-8 w-8 text-white" />
                </div>
                <p className="font-semibold text-[#222222] dark:text-white">Lucy</p>
                <p className="mt-1 text-sm text-[#717171] dark:text-[#a0a0a0]">
                  Send a message to start chatting.
                </p>
                {lucyState && (
                  <p className="mt-2 text-xs text-[#b0b0b0] dark:text-[#666]">
                    {moodEmoji(lucyState.mood)} Feeling {lucyState.mood}
                  </p>
                )}
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
            placeholder="Message Lucy..."
            disabled={isStreaming || connectionStatus !== "connected"}
            className="flex-1"
          />
          {artifacts.length > 0 && (
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowArtifacts(!showArtifacts)}
              aria-label="Toggle artifacts"
              title="View code artifacts"
              className={cn(
                "border-[#dddddd] dark:border-[#444] hover:bg-[#f7f7f7] dark:hover:bg-[#262626]",
                showArtifacts ? "text-[#ff385c]" : "text-[#717171] dark:text-[#a0a0a0]"
              )}
            >
              <FileText className="h-4 w-4" />
            </Button>
          )}
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

      {/* Artifacts panel */}
      {showArtifacts && artifacts.length > 0 && (
        <ArtifactsPanel artifacts={artifacts} onClose={() => setShowArtifacts(false)} />
      )}
      </div>
    </div>
  );
}
