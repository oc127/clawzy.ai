import { useRef, useState, useCallback, useEffect } from "react";
import { getAccessToken } from "@/lib/auth";

export interface MessageUsage {
  credits_used: number;
  tokens_input: number;
  tokens_output: number;
  model: string;
  balance: number;
  routed?: boolean;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  usage?: MessageUsage;
}

export type ConnectionStatus = "connected" | "reconnecting" | "disconnected";

interface UseChatOptions {
  agentId: string;
  conversationId: string | null;
  onConversationCreated?: (id: string) => void;
}

const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000, 30000];

export function useChat({
  agentId,
  conversationId,
  onConversationCreated,
}: UseChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const streamBufferRef = useRef("");
  const onConversationCreatedRef = useRef(onConversationCreated);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Keep callback ref up to date to avoid stale closures
  useEffect(() => {
    onConversationCreatedRef.current = onConversationCreated;
  }, [onConversationCreated]);

  useEffect(() => {
    let unmounted = false;

    function clearReconnectTimer() {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    }

    function connect() {
      if (unmounted) return;

      // Prevent duplicate connections
      const existing = wsRef.current;
      if (existing && (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING)) {
        return;
      }

      const token = getAccessToken();
      if (!token) return;

      setConnectionStatus("reconnecting");

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(
        `${protocol}//${window.location.host}/api/v1/ws/chat/${agentId}?token=${token}`,
      );

      ws.onopen = () => {
        if (unmounted) return;
        setError(null);
        setConnectionStatus("connected");
        reconnectAttemptRef.current = 0;
      };

      ws.onmessage = (event) => {
        let data;
        try {
          data = JSON.parse(event.data);
        } catch {
          return;
        }
        if (data.type === "stream") {
          streamBufferRef.current += data.content;
          const buffered = streamBufferRef.current;
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.role === "assistant") {
              return [
                ...prev.slice(0, -1),
                { ...last, content: buffered },
              ];
            }
            return [...prev, { role: "assistant", content: buffered }];
          });
        } else if (data.type === "done") {
          setIsStreaming(false);
          streamBufferRef.current = "";
          const rawUsage = data.usage;
          const usage: MessageUsage | undefined =
            rawUsage && typeof rawUsage.credits_used === "number"
              ? (rawUsage as MessageUsage)
              : undefined;
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.role === "assistant" && !last.timestamp) {
              return [...prev.slice(0, -1), { ...last, timestamp: new Date().toISOString(), usage }];
            }
            return prev;
          });
          if (data.conversation_id && onConversationCreatedRef.current) {
            onConversationCreatedRef.current(data.conversation_id);
          }
        } else if (data.type === "error") {
          setError(data.message);
          setIsStreaming(false);
        }
      };

      ws.onerror = () => {
        if (!unmounted) setError("Connection error");
      };

      ws.onclose = () => {
        if (unmounted) return;
        const attempt = reconnectAttemptRef.current;
        if (attempt < RECONNECT_DELAYS.length) {
          setConnectionStatus("reconnecting");
          reconnectTimerRef.current = setTimeout(() => {
            reconnectAttemptRef.current = attempt + 1;
            connect();
          }, RECONNECT_DELAYS[attempt]);
        } else {
          setConnectionStatus("disconnected");
        }
      };

      wsRef.current = ws;
    }

    function handleOnline() {
      if (unmounted) return;
      clearReconnectTimer();
      reconnectAttemptRef.current = 0;
      connect();
    }

    function handleVisibilityChange() {
      if (unmounted) return;
      if (
        document.visibilityState === "visible" &&
        (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN)
      ) {
        clearReconnectTimer();
        reconnectAttemptRef.current = 0;
        connect();
      }
    }

    window.addEventListener("online", handleOnline);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    connect();

    return () => {
      unmounted = true;
      window.removeEventListener("online", handleOnline);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      clearReconnectTimer();
      wsRef.current?.close();
    };
  }, [agentId]);

  const sendMessage = useCallback(
    (content: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

      setMessages((prev) => [...prev, { role: "user", content, timestamp: new Date().toISOString() }]);
      setIsStreaming(true);
      streamBufferRef.current = "";

      wsRef.current.send(
        JSON.stringify({
          type: "message",
          content,
          conversation_id: conversationId || undefined,
        }),
      );
    },
    [conversationId],
  );

  const cancelStream = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "cancel" }));
    }
    setIsStreaming(false);
    streamBufferRef.current = "";
    // Finalize the last assistant message with a timestamp
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.role === "assistant" && !last.timestamp) {
        return [...prev.slice(0, -1), { ...last, timestamp: new Date().toISOString() }];
      }
      return prev;
    });
  }, []);

  return { messages, setMessages, isStreaming, error, sendMessage, cancelStream, connectionStatus };
}
