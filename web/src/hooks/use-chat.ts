import { useRef, useState, useCallback, useEffect } from "react";
import { getAccessToken } from "@/lib/auth";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface UseChatOptions {
  agentId: string;
  conversationId: string | null;
  onConversationCreated?: (id: string) => void;
}

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

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(
      `${protocol}//${window.location.host}/api/v1/ws/chat/${agentId}?token=${token}`,
    );

    ws.onopen = () => setError(null);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
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
        if (data.conversation_id && onConversationCreated) {
          onConversationCreated(data.conversation_id);
        }
      } else if (data.type === "error") {
        setError(data.message);
        setIsStreaming(false);
      }
    };

    ws.onerror = () => setError("Connection error");
    ws.onclose = () => {};

    wsRef.current = ws;
    return () => {
      ws.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentId]);

  const sendMessage = useCallback(
    (content: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

      setMessages((prev) => [...prev, { role: "user", content }]);
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

  return { messages, setMessages, isStreaming, error, sendMessage };
}
