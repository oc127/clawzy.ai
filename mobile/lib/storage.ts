import * as SecureStore from "expo-secure-store";

const ACCESS_TOKEN_KEY = "nc_access_token";
const REFRESH_TOKEN_KEY = "nc_refresh_token";

export async function saveTokens(access: string, refresh: string) {
  await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, access);
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refresh);
}

export async function getAccessToken(): Promise<string | null> {
  return SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
}

export async function getRefreshToken(): Promise<string | null> {
  return SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
}

export async function clearTokens() {
  await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
  await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
}

const LOCALE_KEY = "nc_locale";

export async function saveLocale(locale: string) {
  await SecureStore.setItemAsync(LOCALE_KEY, locale);
}

export async function getLocale(): Promise<string | null> {
  return SecureStore.getItemAsync(LOCALE_KEY);
}
