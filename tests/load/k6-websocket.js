/**
 * Clawzy.ai — k6 WebSocket Test
 *
 * Tests WebSocket chat connections under load.
 * Run: k6 run tests/load/k6-websocket.js
 *
 * Environment variables:
 *   K6_BASE_URL      - Backend URL (default: http://localhost:8000)
 *   K6_WS_URL        - WebSocket URL (default: ws://localhost:8000)
 *   K6_TEST_EMAIL    - Test account email
 *   K6_TEST_PASSWORD - Test account password
 *   K6_AGENT_ID      - Agent ID to test with
 */

import http from "k6/http";
import ws from "k6/ws";
import { check, sleep } from "k6";
import { Rate, Counter, Trend } from "k6/metrics";

const BASE_URL = __ENV.K6_BASE_URL || "http://localhost:8000";
const WS_URL = __ENV.K6_WS_URL || "ws://localhost:8000";
const TEST_EMAIL = __ENV.K6_TEST_EMAIL || "loadtest@clawzy.ai";
const TEST_PASSWORD = __ENV.K6_TEST_PASSWORD || "loadtest123";
const AGENT_ID = __ENV.K6_AGENT_ID || "";

const wsErrors = new Rate("ws_errors");
const wsMessages = new Counter("ws_messages_received");
const wsConnectDuration = new Trend("ws_connect_duration");

export const options = {
  stages: [
    { duration: "30s", target: 5 }, // ramp up
    { duration: "1m", target: 20 }, // sustained
    { duration: "30s", target: 0 }, // ramp down
  ],
  thresholds: {
    ws_errors: ["rate<0.1"],
    ws_connect_duration: ["p(95)<3000"],
  },
};

export function setup() {
  // Login to get token
  const loginRes = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email: TEST_EMAIL, password: TEST_PASSWORD }),
    { headers: { "Content-Type": "application/json" } }
  );

  if (loginRes.status !== 200) {
    console.error(`Login failed: HTTP ${loginRes.status}`);
    return { token: null, agentId: AGENT_ID };
  }

  const token = JSON.parse(loginRes.body).access_token;

  // Get first agent if no agent ID specified
  let agentId = AGENT_ID;
  if (!agentId) {
    const agentsRes = http.get(`${BASE_URL}/api/v1/agents`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (agentsRes.status === 200) {
      const agents = JSON.parse(agentsRes.body);
      if (agents.length > 0) {
        agentId = agents[0].id;
      }
    }
  }

  return { token, agentId };
}

export default function (data) {
  if (!data.token || !data.agentId) {
    console.warn("No token or agent ID. Skipping WebSocket test.");
    sleep(1);
    return;
  }

  const wsUrl = `${WS_URL}/api/v1/ws/chat/${data.agentId}?token=${data.token}`;
  const connectStart = Date.now();

  const res = ws.connect(wsUrl, {}, function (socket) {
    wsConnectDuration.add(Date.now() - connectStart);

    socket.on("open", function () {
      // Send a test message
      socket.send(
        JSON.stringify({
          type: "message",
          content: "Hello, this is a load test message.",
        })
      );
    });

    socket.on("message", function (msg) {
      wsMessages.add(1);
      try {
        const data = JSON.parse(msg);
        check(data, {
          "ws message has type": (d) => d.type !== undefined,
        });
      } catch (_e) {
        // Non-JSON messages are acceptable (e.g., keepalive)
      }
    });

    socket.on("error", function (e) {
      wsErrors.add(1);
      console.error(`WebSocket error: ${e.error()}`);
    });

    // Keep connection open for a few seconds to receive stream
    socket.setTimeout(function () {
      socket.close();
    }, 5000);
  });

  check(res, {
    "ws connected": (r) => r && r.status === 101,
  }) || wsErrors.add(1);

  sleep(2);
}
