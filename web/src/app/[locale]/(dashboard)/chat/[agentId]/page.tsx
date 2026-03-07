"use client";

import { useRef, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useChat, type Message } from "@/hooks/useChat";
import { useRhythm } from "@/hooks/useRhythm";
import { listModels, type ModelInfo } from "@/lib/api";
import type { ChatMessage } from "@/lib/ws";
import MessageBubble from "@/components/chat/MessageBubble";
import MessageInput from "@/components/chat/MessageInput";
import CreditsBadge from "@/components/dashboard/CreditsBadge";

export default function ChatPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const t = useTranslations("chat");
  const tc = useTranslations("common");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const addSystemMessageRef = useRef<(content: string) => void>(() => {});
  const prevBalanceRef = useRef<number | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [showConversations, setShowConversations] = useState(false);

  useEffect(() => {
    listModels().then(setModels).catch(() => {});
  }, []);

  const { greeting, onAssistantReply } = useRhythm({
    greetings: {
      morning: t("greetMorning"),
      afternoon: t("greetAfternoon"),
      evening: t("greetEvening"),
      night: t("greetNight"),
    },
    milestones: {
      1: t("milestone1"),
      5: t("milestone5"),
      10: t("milestone10"),
      25: t("milestone25"),
      50: t("milestone50"),
    },
  });

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const handleStatus = useCallback(
    (msg: ChatMessage) => {
      if (msg.message === "agent_starting") {
        addSystemMessageRef.current(t("lobsterWaking"));
      }
      scrollToBottom();
    },
    [scrollToBottom, t],
  );

  const {
    messages,
    streaming,
    connStatus,
    balance,
    currentModel,
    conversations,
    currentConversationId,
    sendMessage,
    addSystemMessage,
    switchModel,
    switchConversation,
    startNewConversation,
  } = useChat({
    agentId,
    onStatus: handleStatus,
    errorFallback: t("errorFallback"),
    reconnectedText: t("reconnected"),
  });

  useEffect(() => {
    addSystemMessageRef.current = addSystemMessage;
  }, [addSystemMessage]);

  // Milestone celebrations: fire when streaming ends (a reply just completed)
  const wasStreamingRef = useRef(false);
  useEffect(() => {
    if (wasStreamingRef.current && !streaming) {
      const milestone = onAssistantReply();
      if (milestone) {
        addSystemMessage(milestone);
        scrollToBottom();
      }
    }
    wasStreamingRef.current = streaming;
  }, [streaming, onAssistantReply, addSystemMessage, scrollToBottom]);

  // Track balance changes for CreditsBadge animation
  const balanceChanged = prevBalanceRef.current !== null && balance !== null && balance !== prevBalanceRef.current;
  useEffect(() => {
    if (balance !== null) {
      prevBalanceRef.current = balance;
    }
  }, [balance]);

  function handleSend(content: string) {
    sendMessage(content);
    scrollToBottom();
  }

  const statusDot = {
    connected: "bg-green-500",
    connecting: "bg-yellow-500 animate-pulse",
    disconnected: "bg-red-500",
  }[connStatus];

  function handleModelChange(model: string) {
    switchModel(model);
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Conversation sidebar */}
      {showConversations && (
        <div className="w-64 border-r border-border flex flex-col bg-surface/50">
          <div className="px-4 py-3.5 border-b border-border flex items-center justify-between">
            <span className="text-xs font-medium text-muted uppercase tracking-wider">{t("conversations")}</span>
            <button
              onClick={() => { startNewConversation(); setShowConversations(false); }}
              className="text-xs text-accent hover:text-accent-hover transition-colors"
            >
              + {t("newConversation")}
            </button>
          </div>
          <div className="flex-1 overflow-y-auto">
            {conversations.length === 0 ? (
              <p className="px-4 py-6 text-xs text-muted text-center">{t("noConversations")}</p>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => { switchConversation(conv.id); setShowConversations(false); }}
                  className={`w-full text-left px-4 py-3 border-b border-border/50 hover:bg-surface-hover transition-colors ${
                    conv.id === currentConversationId ? "bg-surface-hover" : ""
                  }`}
                >
                  <p className="text-sm text-foreground truncate">{conv.title || t("newConversation")}</p>
                  <p className="text-[10px] text-muted mt-0.5">
                    {new Date(conv.updated_at).toLocaleDateString()}
                  </p>
                </button>
              ))
            )}
          </div>
        </div>
      )}

      <div className="flex flex-col flex-1 min-w-0">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setShowConversations((v) => !v)}
            className="text-muted hover:text-foreground transition-colors"
            title={t("conversations")}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M2 4h12M2 8h12M2 12h12" />
            </svg>
          </button>
          <div className={`w-2 h-2 rounded-full ${statusDot}`} />
          <h2 className="text-sm font-medium text-foreground">{t("myLobster")}</h2>
          {models.length > 1 && (
            <select
              value={currentModel}
              onChange={(e) => handleModelChange(e.target.value)}
              disabled={connStatus !== "connected" || streaming}
              className="ml-2 px-2 py-1 bg-surface border border-border rounded text-xs text-muted focus:outline-none focus:border-accent disabled:opacity-40 transition-colors"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          )}
        </div>
        {balance !== null && <CreditsBadge balance={balance} label={tc("energy")} pulse={balanceChanged} />}
      </div>

      {connStatus === "disconnected" && (
        <div className="px-6 py-2 border-b border-border text-center">
          <span className="text-xs text-muted">
            {t("disconnectedMsg")}{" "}
            <button
              onClick={() => window.location.reload()}
              className="text-accent hover:text-accent-hover transition-colors"
            >
              {t("clickRefresh")}
            </button>
          </span>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-3">
        {messages.length === 0 && (
          <div className="text-center pt-20">
            <p className="text-[10px] text-muted/40 uppercase tracking-widest mb-4">{greeting}</p>
            <p className="text-sm text-muted mb-8">{t("emptyPrompt")}</p>
            <div className="flex flex-wrap justify-center gap-2 max-w-md mx-auto">
              {[t("prompt1"), t("prompt2"), t("prompt3")].map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => connStatus === "connected" && handleSend(prompt)}
                  disabled={connStatus !== "connected"}
                  className="px-4 py-2 text-xs text-muted hover:text-foreground border border-border hover:border-accent/40 rounded-full transition-all duration-200 disabled:opacity-30"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg: Message, i: number) => (
          <MessageBubble
            key={`${msg.role}-${i}`}
            role={msg.role}
            content={msg.content}
            isStreaming={streaming && i === messages.length - 1 && msg.role === "assistant"}
            thinkingText={t("thinking")}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <MessageInput
        onSend={handleSend}
        disabled={connStatus !== "connected"}
        streaming={streaming}
        placeholder={connStatus === "connected" ? t("inputPlaceholder") : t("inputConnecting")}
        sendLabel={tc("send")}
      />
      </div>
    </div>
  );
}
