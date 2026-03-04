const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1";

export interface ChatMessage {
  type: "message" | "stream" | "done" | "error" | "agent_status";
  content?: string;
  usage?: { credits: number; balance: number };
  code?: string;
  status?: string;
}

export function createChatSocket(
  agentId: string,
  onMessage: (msg: ChatMessage) => void,
  onClose?: () => void
): WebSocket {
  const token = localStorage.getItem("token") || "";
  const ws = new WebSocket(`${WS_BASE}/ws/chat/${agentId}?token=${token}`);

  ws.onmessage = (event) => {
    try {
      const msg: ChatMessage = JSON.parse(event.data);
      onMessage(msg);
    } catch {
      // ignore non-JSON messages
    }
  };

  ws.onclose = () => {
    onClose?.();
  };

  return ws;
}
