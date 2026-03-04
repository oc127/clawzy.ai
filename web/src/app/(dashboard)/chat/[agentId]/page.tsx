"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { createChatSocket, type ChatMessage } from "@/lib/ws";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [connected, setConnected] = useState(false);
  const [balance, setBalance] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamBufferRef = useRef("");

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    if (!agentId) return;

    const ws = createChatSocket(
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
            if (msg.usage) {
              setBalance(msg.usage.balance);
            }
            break;

          case "error":
            setStreaming(false);
            streamBufferRef.current = "";
            setMessages((prev) => [
              ...prev,
              { role: "assistant", content: `龙虾遇到了点问题: ${msg.content || msg.code || "未知错误"}` },
            ]);
            break;

          case "agent_status":
            // Could update UI status indicator
            break;
        }
        scrollToBottom();
      },
      () => setConnected(false)
    );

    ws.onopen = () => setConnected(true);
    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [agentId, scrollToBottom]);

  function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !wsRef.current || streaming) return;

    const content = input.trim();
    setInput("");

    // Add user message
    setMessages((prev) => [...prev, { role: "user", content }]);

    // Add empty assistant message for streaming
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    streamBufferRef.current = "";
    setStreaming(true);

    wsRef.current.send(JSON.stringify({ type: "message", content }));
    scrollToBottom();
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🦞</span>
          <div>
            <h2 className="text-white font-semibold">我的龙虾</h2>
            <p className="text-xs text-gray-500">
              {connected ? "🟢 在线" : "⚪ 连接中..."}
            </p>
          </div>
        </div>
        {balance !== null && (
          <span className="text-sm text-gray-500">⚡ {balance} 能量</span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-20">
            <div className="text-5xl mb-4">🦞</div>
            <p className="text-gray-500">对龙虾说点什么吧</p>
          </div>
        )}

        {messages.map((msg, i) => (
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
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={sendMessage} className="px-6 py-4 border-t border-gray-800">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="对龙虾说..."
            disabled={!connected}
            className="flex-1 px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!connected || streaming || !input.trim()}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-xl transition"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  );
}
