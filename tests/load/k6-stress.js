/**
 * Clawzy.ai — k6 Stress Test
 *
 * Ramp up load to find the system's breaking point.
 * Run: k6 run tests/load/k6-stress.js
 *
 * Environment variables:
 *   K6_BASE_URL      - Backend URL (default: http://localhost:8000)
 *   K6_TEST_EMAIL    - Test account email
 *   K6_TEST_PASSWORD - Test account password
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.K6_BASE_URL || "http://localhost:8000";
const TEST_EMAIL = __ENV.K6_TEST_EMAIL || "loadtest@clawzy.ai";
const TEST_PASSWORD = __ENV.K6_TEST_PASSWORD || "loadtest123";

const errorRate = new Rate("errors");
const loginDuration = new Trend("login_duration");

export const options = {
  stages: [
    { duration: "1m", target: 10 }, // warm up
    { duration: "2m", target: 50 }, // moderate load
    { duration: "2m", target: 100 }, // high load
    { duration: "1m", target: 200 }, // stress peak
    { duration: "1m", target: 0 }, // cool down
  ],
  thresholds: {
    http_req_duration: ["p(95)<2000"],
    http_req_failed: ["rate<0.05"],
    errors: ["rate<0.05"],
  },
};

export function setup() {
  const loginRes = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email: TEST_EMAIL, password: TEST_PASSWORD }),
    { headers: { "Content-Type": "application/json" } }
  );

  if (loginRes.status === 200) {
    return { token: JSON.parse(loginRes.body).access_token };
  }
  console.warn(`Login failed (HTTP ${loginRes.status}).`);
  return { token: null };
}

export default function (data) {
  // Mix of unauthenticated and authenticated requests

  // Health check (lightweight, frequent)
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    "health ok": (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(0.2);

  // Login attempt (heavy, less frequent)
  if (Math.random() < 0.3) {
    const start = Date.now();
    const loginRes = http.post(
      `${BASE_URL}/api/v1/auth/login`,
      JSON.stringify({ email: TEST_EMAIL, password: TEST_PASSWORD }),
      { headers: { "Content-Type": "application/json" } }
    );
    loginDuration.add(Date.now() - start);
    check(loginRes, {
      "login responds": (r) => r.status === 200 || r.status === 401 || r.status === 429,
    }) || errorRate.add(1);
  }

  sleep(0.3);

  // Authenticated requests
  if (data.token) {
    const authHeaders = {
      Authorization: `Bearer ${data.token}`,
      "Content-Type": "application/json",
    };

    // Agents list
    const agentsRes = http.get(`${BASE_URL}/api/v1/agents`, {
      headers: authHeaders,
    });
    check(agentsRes, {
      "agents ok": (r) => r.status === 200 || r.status === 429,
    }) || errorRate.add(1);

    sleep(0.2);

    // Models list
    if (Math.random() < 0.5) {
      const modelsRes = http.get(`${BASE_URL}/api/v1/models`, {
        headers: authHeaders,
      });
      check(modelsRes, {
        "models ok": (r) => r.status === 200 || r.status === 429,
      }) || errorRate.add(1);
    }
  }

  // Status page
  const statusRes = http.get(`${BASE_URL}/status`);
  check(statusRes, {
    "status ok": (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(0.5);
}
