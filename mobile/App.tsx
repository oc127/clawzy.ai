import React, { useRef, useState, useCallback } from "react";
import {
  ActivityIndicator,
  BackHandler,
  Platform,
  SafeAreaView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { WebView } from "react-native-webview";
import { WebViewNavigation } from "react-native-webview/lib/WebViewTypes";

// ─── Config ──────────────────────────────────────────────────────────────────
// Dev: replace with your machine's LAN IP, e.g. "http://192.168.1.100"
// Prod: "https://www.nipponclaw.com"
const WEB_URL = __DEV__ ? "http://192.168.1.100" : "https://www.nipponclaw.com";

// ─── Colours (matches web dark theme) ────────────────────────────────────────
const COLORS = {
  bg: "#111114",
  card: "#1c1c21",
  primary: "#ff5a5f",
  muted: "#a8a5a0",
  border: "#2d2d33",
};

// ─── Loading Overlay ─────────────────────────────────────────────────────────
function LoadingScreen() {
  return (
    <View style={styles.loadingContainer}>
      <ActivityIndicator size="large" color={COLORS.primary} />
      <Text style={styles.loadingText}>NipponClaw</Text>
    </View>
  );
}

// ─── Error Screen ─────────────────────────────────────────────────────────────
function ErrorScreen({ onRetry }: { onRetry: () => void }) {
  return (
    <View style={styles.errorContainer}>
      <Text style={styles.errorEmoji}>🦞</Text>
      <Text style={styles.errorTitle}>Connection failed</Text>
      <Text style={styles.errorSubtitle}>
        Make sure the server is running and you're on the same network.
      </Text>
      <TouchableOpacity style={styles.retryButton} onPress={onRetry}>
        <Text style={styles.retryText}>Retry</Text>
      </TouchableOpacity>
    </View>
  );
}

// ─── Main App ────────────────────────────────────────────────────────────────
export default function App() {
  const webViewRef = useRef<WebView>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [canGoBack, setCanGoBack] = useState(false);

  // Android hardware back button
  const handleAndroidBack = useCallback(() => {
    if (canGoBack && webViewRef.current) {
      webViewRef.current.goBack();
      return true;
    }
    return false;
  }, [canGoBack]);

  React.useEffect(() => {
    if (Platform.OS === "android") {
      BackHandler.addEventListener("hardwareBackPress", handleAndroidBack);
      return () =>
        BackHandler.removeEventListener("hardwareBackPress", handleAndroidBack);
    }
  }, [handleAndroidBack]);

  const handleNavigationChange = (state: WebViewNavigation) => {
    setCanGoBack(state.canGoBack);
  };

  const handleRetry = () => {
    setError(false);
    setLoading(true);
    webViewRef.current?.reload();
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.bg} />

      {error ? (
        <ErrorScreen onRetry={handleRetry} />
      ) : (
        <>
          <WebView
            ref={webViewRef}
            source={{ uri: WEB_URL }}
            style={styles.webview}
            // Allow all content (needed for WebSocket)
            originWhitelist={["*"]}
            // WebSocket support
            javaScriptEnabled
            domStorageEnabled
            // iOS overscroll
            bounces={false}
            // Loading
            onLoadStart={() => setLoading(true)}
            onLoadEnd={() => setLoading(false)}
            onError={() => {
              setLoading(false);
              setError(true);
            }}
            onHttpError={(e) => {
              if (e.nativeEvent.statusCode >= 500) {
                setError(true);
              }
            }}
            onNavigationStateChange={handleNavigationChange}
            // Allow localStorage / cookies
            sharedCookiesEnabled
            // iOS scroll indicator
            showsVerticalScrollIndicator={false}
          />
          {loading && (
            <View style={styles.loadingOverlay}>
              <LoadingScreen />
            </View>
          )}
        </>
      )}
    </SafeAreaView>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  webview: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: COLORS.bg,
    justifyContent: "center",
    alignItems: "center",
  },
  loadingContainer: {
    alignItems: "center",
    gap: 16,
  },
  loadingText: {
    color: COLORS.muted,
    fontSize: 14,
    fontWeight: "500",
    letterSpacing: 0.5,
  },
  errorContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
    gap: 12,
  },
  errorEmoji: {
    fontSize: 48,
    marginBottom: 8,
  },
  errorTitle: {
    color: "#f0eeeb",
    fontSize: 20,
    fontWeight: "700",
  },
  errorSubtitle: {
    color: COLORS.muted,
    fontSize: 14,
    textAlign: "center",
    lineHeight: 20,
  },
  retryButton: {
    marginTop: 16,
    backgroundColor: COLORS.primary,
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 12,
  },
  retryText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "600",
  },
});
