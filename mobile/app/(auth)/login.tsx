import React, { useState } from "react";
import {
  View, Text, ScrollView, TouchableOpacity,
  KeyboardAvoidingView, Platform, StyleSheet,
} from "react-native";
import { Link } from "expo-router";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Logo } from "@/components/Logo";
import { colors, spacing, radius, typography } from "@/lib/theme";

export default function LoginScreen() {
  const { login } = useAuth();
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) return;
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : t.common.error);
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
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View style={styles.header}>
          <Logo size="lg" />
        </View>

        {/* Card */}
        <View style={styles.card}>
          <Text style={styles.title}>{t.auth.login.title}</Text>
          <Text style={styles.subtitle}>{t.auth.login.subtitle}</Text>

          {error ? (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : null}

          <View style={styles.form}>
            <Input
              label={t.auth.login.email}
              placeholder="you@example.com"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              textContentType="emailAddress"
            />
            <Input
              label={t.auth.login.password}
              placeholder="••••••••"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              textContentType="password"
            />
          </View>

          <Link href="/(auth)/forgot-password" asChild>
            <TouchableOpacity style={styles.forgotLink}>
              <Text style={styles.forgotText}>{t.auth.login.forgotPassword}</Text>
            </TouchableOpacity>
          </Link>

          <Button
            onPress={handleLogin}
            loading={loading}
            disabled={!email || !password}
            size="lg"
            style={styles.submitBtn}
          >
            {t.auth.login.submit}
          </Button>

          <View style={styles.footer}>
            <Text style={styles.footerText}>{t.auth.login.noAccount} </Text>
            <Link href="/(auth)/register" asChild>
              <TouchableOpacity>
                <Text style={styles.link}>{t.auth.login.signup}</Text>
              </TouchableOpacity>
            </Link>
          </View>
        </View>

        {/* Bottom decoration */}
        <View style={styles.statsRow}>
          {[["500", t.auth.login.stat1], ["6+", t.auth.login.stat2], ["24/7", t.auth.login.stat3]].map(([val, label]) => (
            <View key={label} style={styles.statItem}>
              <Text style={styles.statVal}>{val}</Text>
              <Text style={styles.statLabel}>{label}</Text>
            </View>
          ))}
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
    paddingTop: 80,
    paddingBottom: 40,
  },
  header: {
    alignItems: "center",
    marginBottom: 40,
  },
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
  title: {
    ...typography.xl,
    ...typography.extrabold,
    color: colors.text,
    marginBottom: 4,
  },
  subtitle: {
    ...typography.base,
    color: colors.textSecondary,
    marginBottom: 24,
  },
  errorBox: {
    backgroundColor: colors.errorLight,
    borderWidth: 1,
    borderColor: colors.errorBorder,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  errorText: { ...typography.sm, color: colors.error },
  form: { gap: 16, marginBottom: 8 },
  forgotLink: { alignSelf: "flex-end", marginBottom: 12 },
  forgotText: { ...typography.sm, color: colors.primary, fontWeight: "600" },
  submitBtn: { marginBottom: 16 },
  footer: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    marginTop: 4,
  },
  footerText: { ...typography.sm, color: colors.textSecondary },
  link: { ...typography.sm, ...typography.bold, color: colors.primary },
  statsRow: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 32,
    marginTop: 32,
  },
  statItem: { alignItems: "center", gap: 2 },
  statVal: { ...typography.lg, ...typography.extrabold, color: colors.primary },
  statLabel: { ...typography.xs, color: colors.textMuted },
});
