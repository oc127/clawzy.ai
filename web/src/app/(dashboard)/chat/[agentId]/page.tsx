"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { createChatSocket, type ChatMessage, type ChatSocket } from "@/lib/ws";
import { listConversations, listMessages } from "@/lib/api";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

type ConnectionStatus = "connected" | "connecting" | "disconnected";

export default function ChatPage() {
  const { agentId } = useParams<{ agentId: string }>();
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

  // Load conversation history on mount
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
      .catch(() => {
        // No history — that's fine
      });
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
            // 错误消息用龙虾口吻展示，不显示 error code
            setMessages((prev) => [
              ...prev,
              { role: "assistant", content: msg.content || "龙虾遇到了点小问题，稍后再试试吧 🦞" },
            ]);
            break;

          case "agent_status":
            // 重连中的状态提示
            if (msg.status === "reconnecting") {
              setMessages((prev) => {
                // 更新最后一条系统消息，避免刷屏
                const last = prev[prev.length - 1];
                if (last?.role === "system") {
                  return [...prev.slice(0, -1), { role: "system", content: msg.content || "" }];
                }
                return [...prev, { role: "system", content: msg.content || "" }];
              });
            }
            break;

          case "reconnected":
            // 重连成功，移除系统消息，显示龙虾回来了
            setMessages((prev) => {
              const filtered = prev.filter((m) => m.role !== "system");
              return [...filtered, { role: "assistant", content: msg.content || "我回来了 🦞" }];
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
  }, [agentId, scrollToBottom]);

  function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !socketRef.current || streaming || connStatus !== "connected") return;

    const content = input.trim();
    setInput("");

    // Add user message
    setMessages((prev) => [...prev, { role: "user", content }]);

    // Add empty assistant message for streaming
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    streamBufferRef.current = "";
    setStreaming(true);

    socketRef.current.send({ type: "message", content });
    scrollToBottom();
  }

  const statusLabel = {
    connected: "🟢 在线",
    connecting: "🟡 连接中...",
    disconnected: "🔴 断开",
  }[connStatus];

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🦞</span>
          <div>
            <h2 className="text-white font-semibold">我的龙虾</h2>
            <p className="text-xs text-gray-500">{statusLabel}</p>
          </div>
        </div>
        {balance !== null && (
          <span className="text-sm text-gray-500">⚡ {balance} 能量</span>
        )}
      </div>

      {/* 断线提示条 */}
      {connStatus === "connecting" && (
        <div className="bg-yellow-900/30 border-b border-yellow-700 px-6 py-2 text-sm text-yellow-300 text-center">
          龙虾正在重新连接...
        </div>
      )}
      {connStatus === "disconnected" && (
        <div className="bg-red-900/30 border-b border-red-700 px-6 py-2 text-sm text-red-300 text-center">
          连接已断开 —{" "}
          <button
            onClick={() => window.location.reload()}
            className="underline hover:text-red-200"
          >
            点击刷新
          </button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-20">
            <div className="text-5xl mb-4">🦞</div>
            <p className="text-gray-500">对龙虾说点什么吧</p>
          </div>
        )}

        {messages.map((msg, i) => {
          // 系统消息（重连提示）
          if (msg.role === "system") {
            return (
              <div key={i} className="text-center">
                <span className="text-xs text-gray-600 bg-gray-900 px-3 py-1 rounded-full">
                  {msg.content}
                </span>
              </div>
            );
          }

          return (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-800 text-gray-100"
                }`}
              >
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {msg.content || (streaming && i === messages.length - 1 ? "🦞 思考中..." : "")}
                </p>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={sendMessage} className="px-6 py-4 border-t border-gray-800">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={connStatus === "connected" ? "对龙虾说..." : "龙虾正在连接中..."}
            disabled={connStatus !== "connected"}
            className="flex-1 px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={connStatus !== "connected" || streaming || !input.trim()}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-xl transition"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  );
}
