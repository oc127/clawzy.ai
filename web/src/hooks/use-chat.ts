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

interface UseChatOptions {
  agentId: string;
  conversationId: string | null;
  onConversationCreated?: (id: string) => void;
}

const RECONNECT_DELAYS = [1000, 2000, 4000, 8000];

export function useChat({
  agentId,
  conversationId,
  onConversationCreated,
}: UseChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
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

    function connect() {
      const token = getAccessToken();
      if (!token || unmounted) return;

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(
        `${protocol}//${window.location.host}/api/v1/ws/chat/${agentId}?token=${token}`,
      );

      ws.onopen = () => {
        setError(null);
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
          const usage = data.usage as MessageUsage | undefined;
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

      ws.onerror = () => setError("Connection error");

      ws.onclose = () => {
        if (unmounted) return;
        const attempt = reconnectAttemptRef.current;
        if (attempt < RECONNECT_DELAYS.length) {
          reconnectTimerRef.current = setTimeout(() => {
            reconnectAttemptRef.current = attempt + 1;
            connect();
          }, RECONNECT_DELAYS[attempt]);
        } else {
          setError("Connection lost. Please refresh the page.");
        }
      };

      wsRef.current = ws;
    }

    connect();

    return () => {
      unmounted = true;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
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

  return { messages, setMessages, isStreaming, error, sendMessage, cancelStream };
}
