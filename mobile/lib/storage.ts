// Temporary in-memory storage for development
// Replace with expo-secure-store once SDK compatibility is confirmed
const store: Record<string, string> = {};

export async function saveTokens(access: string, refresh: string) {
  store["access_token"] = access;
  store["refresh_token"] = refresh;
}

export async function getAccessToken(): Promise<string | null> {
  return store["access_token"] ?? null;
}

export async function getRefreshToken(): Promise<string | null> {
  return store["refresh_token"] ?? null;
}

export async function clearTokens() {
  delete store["access_token"];
  delete store["refresh_token"];
}

export async function saveLocale(locale: string) {
  store["locale"] = locale;
}

export async function getLocale(): Promise<string | null> {
  return store["locale"] ?? null;
}
