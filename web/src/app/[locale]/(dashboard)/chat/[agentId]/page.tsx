"use client";

import { useRef, useCallback, useEffect } from "react";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useChat, type Message } from "@/hooks/useChat";
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
    sendMessage,
    addSystemMessage,
  } = useChat({
    agentId,
    onStatus: handleStatus,
    errorFallback: t("errorFallback"),
    reconnectedText: t("reconnected"),
  });

  useEffect(() => {
    addSystemMessageRef.current = addSystemMessage;
  }, [addSystemMessage]);

  function handleSend(content: string) {
    sendMessage(content);
    scrollToBottom();
  }

  const statusDot = {
    connected: "bg-green-500",
    connecting: "bg-yellow-500 animate-pulse",
    disconnected: "bg-red-500",
  }[connStatus];

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className={`w-2 h-2 rounded-full ${statusDot}`} />
          <h2 className="text-sm font-medium text-foreground">{t("myLobster")}</h2>
        </div>
        {balance !== null && <CreditsBadge balance={balance} label={tc("energy")} />}
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
          <div className="text-center pt-28">
            <div className="animate-breathe mb-4">
              <span className="text-4xl">🦞</span>
            </div>
            <p className="text-sm text-muted">{t("emptyPrompt")}</p>
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
  );
}
