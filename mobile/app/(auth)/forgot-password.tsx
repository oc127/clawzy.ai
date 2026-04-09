import React, { useState } from "react";
import {
  View, Text, ScrollView, TouchableOpacity,
  KeyboardAvoidingView, Platform, StyleSheet,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { router } from "expo-router";
import { useLanguage } from "@/context/LanguageContext";
import { apiPost } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Logo } from "@/components/Logo";
import { colors, spacing, radius, typography } from "@/lib/theme";

export default function ForgotPasswordScreen() {
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!email) return;
    setError("");
    setLoading(true);
    try {
      await apiPost("/auth/forgot-password", { email });
      setSent(true);
    } catch {
      setError(t.common.error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView
        contentContainerStyle={[styles.container, { paddingTop: insets.top + spacing.sm }]}
        keyboardShouldPersistTaps="handled"
      >
        <TouchableOpacity
          style={styles.topBack}
          onPress={() => {
            if (router.canGoBack()) router.back();
            else router.replace("/(auth)/login");
          }}
          hitSlop={{ top: 12, bottom: 12, left: 8, right: 8 }}
          accessibilityRole="button"
          accessibilityLabel={t.common.back}
        >
          <Text style={styles.topBackChevron}>←</Text>
          <Text style={styles.topBackText}>{t.common.back}</Text>
        </TouchableOpacity>

        <View style={styles.header}>
          <Logo size="lg" />
        </View>

        <View style={styles.card}>
          <Text style={styles.title}>{t.auth.forgotPassword.title}</Text>
          <Text style={styles.subtitle}>{t.auth.forgotPassword.subtitle}</Text>

          {sent ? (
            <View style={styles.successBox}>
              <Text style={styles.successText}>{t.auth.forgotPassword.sent}</Text>
            </View>
          ) : (
            <>
              {error ? (
                <View style={styles.errorBox}>
                  <Text style={styles.errorText}>{error}</Text>
                </View>
              ) : null}

              <View style={styles.form}>
                <Input
                  label={t.auth.forgotPassword.email}
                  placeholder="you@example.com"
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  textContentType="emailAddress"
                />
              </View>

              <Button
                onPress={handleSubmit}
                loading={loading}
                disabled={!email}
                size="lg"
                style={styles.submitBtn}
              >
                {t.auth.forgotPassword.submit}
              </Button>
            </>
          )}

          <TouchableOpacity
            style={styles.backLink}
            onPress={() => {
              if (router.canGoBack()) router.back();
              else router.replace("/(auth)/login");
            }}
          >
            <Text style={styles.backLinkText}>{t.auth.forgotPassword.backToLogin}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  container: {
    flexGrow: 1,
    paddingHorizontal: spacing.xl,
    paddingBottom: 40,
  },
  topBack: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    marginBottom: spacing.md,
    gap: 4,
  },
  topBackChevron: { fontSize: 20, color: colors.primary, fontWeight: "600" },
  topBackText: { ...typography.base, color: colors.primary, fontWeight: "600" },
  header: { alignItems: "center", marginBottom: 40 },
  card: {
    backgroundColor: colors.white,
    borderRadius: radius.xl + 4,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.xxl,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 20,
    elevation: 6,
  },
  title: { ...typography.xl, ...typography.extrabold, color: colors.text, marginBottom: 4 },
  subtitle: { ...typography.base, color: colors.textSecondary, marginBottom: 24 },
  errorBox: {
    backgroundColor: colors.errorLight,
    borderWidth: 1,
    borderColor: colors.errorBorder,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  errorText: { ...typography.sm, color: colors.error },
  successBox: {
    backgroundColor: "#F0FDF4",
    borderWidth: 1,
    borderColor: "#BBF7D0",
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  successText: { ...typography.sm, color: "#16A34A" },
  form: { gap: 16, marginBottom: 20 },
  submitBtn: { marginBottom: 16 },
  backLink: { alignItems: "center", marginTop: 4 },
  backLinkText: { ...typography.sm, ...typography.bold, color: colors.primary },
});
