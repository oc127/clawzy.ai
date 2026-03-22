import * as SecureStore from "expo-secure-store";

const K = {
  access: "nipponclaw_access_token",
  refresh: "nipponclaw_refresh_token",
  locale: "nipponclaw_locale",
} as const;

export async function saveTokens(access: string, refresh: string) {
  await SecureStore.setItemAsync(K.access, access);
  await SecureStore.setItemAsync(K.refresh, refresh);
}

export async function getAccessToken(): Promise<string | null> {
  return SecureStore.getItemAsync(K.access);
}

export async function getRefreshToken(): Promise<string | null> {
  return SecureStore.getItemAsync(K.refresh);
}

export async function clearTokens() {
  await SecureStore.deleteItemAsync(K.access);
  await SecureStore.deleteItemAsync(K.refresh);
}

export async function saveLocale(locale: string) {
  await SecureStore.setItemAsync(K.locale, locale);
}

export async function getLocale(): Promise<string | null> {
  return SecureStore.getItemAsync(K.locale);
}
