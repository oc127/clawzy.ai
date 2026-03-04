"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { createChatSocket, type ChatMessage, type ChatSocket } from "@/lib/ws";
import { listConversations, listMessages } from "@/lib/api";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

type ConnectionStatus = "connected" | "connecting" | "disconnected";

export default function ChatPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const t = useTranslations("chat");
  const tc = useTranslations("common");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [connStatus, setConnStatus] = useState<ConnectionStatus>("connecting");
  const [balance, setBalance] = useState<number | null>(null);
  const socketRef = useRef<ChatSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamBufferRef = useRef("");

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    if (!agentId) return;
    listConversations(agentId)
      .then((convs) => {
        if (convs.length > 0) {
          return listMessages(convs[0].id, 50);
        }
        return [];
      })
      .then((msgs) => {
        if (msgs.length > 0) {
          setMessages(
            msgs.map((m) => ({ role: m.role as "user" | "assistant", content: m.content }))
          );
          scrollToBottom();
        }
      })
      .catch(() => {});
  }, [agentId, scrollToBottom]);

  useEffect(() => {
    if (!agentId) return;

    const socket = createChatSocket(
      agentId,
      (msg: ChatMessage) => {
        switch (msg.type) {
          case "stream":
            streamBufferRef.current += msg.content || "";
            setMessages((prev) => {
              const updated = [...prev];
              if (updated.length > 0 && updated[updated.length - 1].role === "assistant") {
                updated[updated.length - 1] = {
                  role: "assistant",
                  content: streamBufferRef.current,
                };
              }
              return updated;
            });
            break;

          case "done":
            setStreaming(false);
            streamBufferRef.current = "";
            if (msg.usage?.balance != null) {
              setBalance(msg.usage.balance);
            }
            break;

          case "error":
            setStreaming(false);
            streamBufferRef.current = "";
            setMessages((prev) => [
              ...prev,
              { role: "assistant", content: msg.content || t("errorFallback") },
            ]);
            break;

          case "agent_status":
            if (msg.status === "reconnecting") {
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last?.role === "system") {
                  return [...prev.slice(0, -1), { role: "system", content: msg.content || "" }];
                }
                return [...prev, { role: "system", content: msg.content || "" }];
              });
            }
            break;

          case "reconnected":
            setMessages((prev) => {
              const filtered = prev.filter((m) => m.role !== "system");
              return [...filtered, { role: "assistant", content: msg.content || t("reconnected") }];
            });
            break;
        }
        scrollToBottom();
      },
      setConnStatus,
    );

    socketRef.current = socket;

    return () => {
      socket.close();
    };
  }, [agentId, scrollToBottom, t]);

  function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !socketRef.current || streaming || connStatus !== "connected") return;

    const content = input.trim();
    setInput("");

    setMessages((prev) => [...prev, { role: "user", content }]);
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    streamBufferRef.current = "";
    setStreaming(true);

    socketRef.current.send({ type: "message", content });
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
        {balance !== null && (
          <span className="text-xs text-muted">{balance} {tc("energy")}</span>
        )}
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
          <div className="text-center pt-32">
            <p className="text-sm text-muted">{t("emptyPrompt")}</p>
          </div>
        )}

        {messages.map((msg, i) => {
          if (msg.role === "system") {
            return (
              <div key={i} className="text-center py-1">
                <span className="text-xs text-muted">{msg.content}</span>
              </div>
            );
          }

          return (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[65%] rounded-xl px-4 py-2.5 ${
                  msg.role === "user"
                    ? "bg-accent text-white"
                    : "bg-surface text-foreground"
                }`}
              >
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {msg.content || (streaming && i === messages.length - 1 ? t("thinking") : "")}
                </p>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={sendMessage} className="px-6 py-4 border-t border-border">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={connStatus === "connected" ? t("inputPlaceholder") : t("inputConnecting")}
            disabled={connStatus !== "connected"}
            className="flex-1 px-4 py-2.5 bg-surface border border-border rounded-lg text-foreground placeholder-muted text-sm focus:outline-none focus:border-accent disabled:opacity-40 transition-colors"
          />
          <button
            type="submit"
            disabled={connStatus !== "connected" || streaming || !input.trim()}
            className="px-5 py-2.5 bg-accent hover:bg-accent-hover disabled:bg-surface disabled:text-muted text-white text-sm font-medium rounded-lg transition-colors"
          >
            {tc("send")}
          </button>
        </div>
      </form>
    </div>
  );
}
