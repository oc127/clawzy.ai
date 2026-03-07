/**
 * WebSocket 客户端 — 带自动重连和友好断线提示
 *
 * 断线后自动重连（指数退避），重连期间告诉用户"龙虾正在重新连接"，
 * 而不是让页面默默挂掉。
 */

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1";

const MAX_RECONNECT_ATTEMPTS = 10;
const BASE_DELAY_MS = 1000;

export interface ChatMessage {
  type: "message" | "stream" | "done" | "error" | "status" | "agent_status" | "model_switched" | "pong" | "reconnected";
  content?: string;
  message?: string;
  usage?: { credits: number; balance: number | null };
  code?: string;
  status?: string;
  model?: string;
  is_fallback?: boolean;
  conversation_id?: string;
}

export interface ChatSocket {
  send: (data: object) => void;
  close: () => void;
}

function getLocaleFromCookie(): string {
  if (typeof document === "undefined") return "zh";
  const match = document.cookie.match(/(?:^|;\s*)locale=([^;]*)/);
  return match ? match[1] : "zh";
}

export function createChatSocket(
  agentId: string,
  onMessage: (msg: ChatMessage) => void,
  onStatusChange?: (status: "connected" | "connecting" | "disconnected") => void,
): ChatSocket {
  let ws: WebSocket | null = null;
  let reconnectAttempts = 0;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let intentionallyClosed = false;
  let pingInterval: ReturnType<typeof setInterval> | null = null;

  function connect() {
    const token = localStorage.getItem("token") || "";
    const locale = getLocaleFromCookie();
    onStatusChange?.("connecting");

    ws = new WebSocket(`${WS_BASE}/ws/chat/${agentId}?token=${token}&locale=${locale}`);

    ws.onopen = () => {
      reconnectAttempts = 0;
      onStatusChange?.("connected");

      // 心跳保活：每 30 秒发一个 ping
      pingInterval = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 30_000);
    };

    ws.onmessage = (event) => {
      try {
        const msg: ChatMessage = JSON.parse(event.data);
        // 忽略 pong 心跳回复
        if (msg.type !== "pong") {
          onMessage(msg);
        }
      } catch {
        // ignore non-JSON messages
      }
    };

    ws.onclose = (event) => {
      if (pingInterval) {
        clearInterval(pingInterval);
        pingInterval = null;
      }

      if (intentionallyClosed) {
        onStatusChange?.("disconnected");
        return;
      }

      // 非正常关闭 → 自动重连
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(
          BASE_DELAY_MS * Math.pow(2, reconnectAttempts),
          30_000
        );
        reconnectAttempts++;
        onStatusChange?.("connecting");

        reconnectTimer = setTimeout(connect, delay);
      } else {
        // 彻底失败
        onStatusChange?.("disconnected");
      }
    };

    ws.onerror = () => {
      // onerror 之后会触发 onclose，在 onclose 里处理重连
    };
  }

  connect();

  return {
    send: (data: object) => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
      }
    },
    close: () => {
      intentionallyClosed = true;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      if (pingInterval) {
        clearInterval(pingInterval);
      }
      ws?.close();
    },
  };
}
