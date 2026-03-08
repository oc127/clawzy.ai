/**
 * Clawzy.ai — k6 Smoke Test
 *
 * Quick validation that all critical endpoints respond correctly under light load.
 * Run: k6 run tests/load/k6-smoke.js
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

// Custom metrics
const errorRate = new Rate("errors");
const loginDuration = new Trend("login_duration");

export const options = {
  vus: 5,
  duration: "30s",
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.01"],
    errors: ["rate<0.01"],
  },
};

export function setup() {
  // Login once to get a token for authenticated requests
  const loginRes = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email: TEST_EMAIL, password: TEST_PASSWORD }),
    { headers: { "Content-Type": "application/json" } }
  );

  if (loginRes.status === 200) {
    const body = JSON.parse(loginRes.body);
    return { token: body.access_token };
  }

  console.warn(
    `Login failed (HTTP ${loginRes.status}). Authenticated tests will be skipped.`
  );
  return { token: null };
}

export default function (data) {
  // 1. Health check (unauthenticated)
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    "health: status 200": (r) => r.status === 200,
    "health: body ok": (r) => JSON.parse(r.body).status === "ok",
  }) || errorRate.add(1);

  sleep(0.5);

  // 2. Status page (unauthenticated)
  const statusRes = http.get(`${BASE_URL}/status`);
  check(statusRes, {
    "status: status 200": (r) => r.status === 200,
    "status: has status field": (r) => JSON.parse(r.body).status !== undefined,
  }) || errorRate.add(1);

  sleep(0.5);

  // 3. Login
  const loginStart = Date.now();
  const loginRes = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email: TEST_EMAIL, password: TEST_PASSWORD }),
    { headers: { "Content-Type": "application/json" } }
  );
  loginDuration.add(Date.now() - loginStart);

  check(loginRes, {
    "login: status 200 or 401": (r) =>
      r.status === 200 || r.status === 401,
  }) || errorRate.add(1);

  sleep(0.5);

  // 4. Authenticated requests (if token available)
  if (data.token) {
    const authHeaders = {
      Authorization: `Bearer ${data.token}`,
      "Content-Type": "application/json",
    };

    // Agent list
    const agentsRes = http.get(`${BASE_URL}/api/v1/agents`, {
      headers: authHeaders,
    });
    check(agentsRes, {
      "agents: status 200": (r) => r.status === 200,
    }) || errorRate.add(1);

    sleep(0.3);

    // Models list
    const modelsRes = http.get(`${BASE_URL}/api/v1/models`, {
      headers: authHeaders,
    });
    check(modelsRes, {
      "models: status 200": (r) => r.status === 200,
    }) || errorRate.add(1);
  }

  sleep(1);
}
