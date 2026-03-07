"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { createChatSocket, type ChatMessage, type ChatSocket } from "@/lib/ws";
import { listConversations, listMessages, type ConversationInfo } from "@/lib/api";

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export type ConnectionStatus = "connected" | "connecting" | "disconnected";

interface UseChatOptions {
  agentId: string;
  initialModel?: string;
  onStatus?: (msg: ChatMessage) => void;
  errorFallback?: string;
  reconnectedText?: string;
}

export function useChat({ agentId, initialModel, onStatus, errorFallback, reconnectedText }: UseChatOptions) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [connStatus, setConnStatus] = useState<ConnectionStatus>("connecting");
  const [balance, setBalance] = useState<number | null>(null);
  const [currentModel, setCurrentModel] = useState(initialModel || "deepseek-chat");
  const [conversations, setConversations] = useState<ConversationInfo[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const socketRef = useRef<ChatSocket | null>(null);
  const streamBufferRef = useRef("");

  const scrollToBottom = useCallback(() => {
    // Caller can handle scrolling via ref
  }, []);

  // Load conversation history
  useEffect(() => {
    if (!agentId) return;
    listConversations(agentId)
      .then((convs) => {
        setConversations(convs);
        if (convs.length > 0) {
          setCurrentConversationId(convs[0].id);
          return listMessages(convs[0].id, 50);
        }
        return [];
      })
      .then((msgs) => {
        if (msgs.length > 0) {
          setMessages(
            msgs.map((m) => ({ role: m.role as "user" | "assistant", content: m.content }))
          );
        }
      })
      .catch((e: unknown) => console.error("Failed to load chat history:", e));
  }, [agentId]);

  // WebSocket connection
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
            // Track conversation_id from backend and refresh list
            if (msg.conversation_id) {
              setCurrentConversationId(msg.conversation_id);
              listConversations(agentId)
                .then(setConversations)
                .catch(() => {});
            }
            break;

          case "error":
            setStreaming(false);
            streamBufferRef.current = "";
            setMessages((prev) => [
              ...prev,
              { role: "assistant", content: msg.content || msg.message || errorFallback || "" },
            ]);
            break;

          case "status":
            onStatus?.(msg);
            break;

          case "model_switched":
            if (msg.model) {
              setCurrentModel(msg.model);
            }
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
              return [...filtered, { role: "assistant", content: msg.content || reconnectedText || "" }];
            });
            break;
        }
      },
      setConnStatus,
    );

    socketRef.current = socket;

    return () => {
      socket.close();
    };
  }, [agentId, onStatus, errorFallback, reconnectedText]);

  const sendMessage = useCallback(
    (content: string) => {
      if (!content.trim() || !socketRef.current || streaming || connStatus !== "connected") return;

      setMessages((prev) => [...prev, { role: "user", content }]);
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
      streamBufferRef.current = "";
      setStreaming(true);

      socketRef.current.send({ type: "message", content });
    },
    [streaming, connStatus],
  );

  const addSystemMessage = useCallback((content: string) => {
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last?.role === "system") {
        return [...prev.slice(0, -1), { role: "system", content }];
      }
      return [...prev, { role: "system", content }];
    });
  }, []);

  const clearSystemMessages = useCallback(() => {
    setMessages((prev) => prev.filter((m) => m.role !== "system"));
  }, []);

  const switchModel = useCallback(
    (model: string) => {
      if (!socketRef.current || connStatus !== "connected") return;
      socketRef.current.send({ type: "switch_model", model });
    },
    [connStatus],
  );

  const switchConversation = useCallback(
    async (conversationId: string) => {
      try {
        const msgs = await listMessages(conversationId, 50);
        setMessages(
          msgs.map((m) => ({ role: m.role as "user" | "assistant", content: m.content }))
        );
        setCurrentConversationId(conversationId);
      } catch (e: unknown) {
        console.error("Failed to load conversation:", e);
      }
    },
    [],
  );

  const startNewConversation = useCallback(() => {
    setMessages([]);
    setCurrentConversationId(null);
  }, []);

  return {
    messages,
    input,
    setInput,
    streaming,
    connStatus,
    balance,
    currentModel,
    conversations,
    currentConversationId,
    sendMessage,
    addSystemMessage,
    clearSystemMessages,
    switchModel,
    switchConversation,
    startNewConversation,
  };
}
