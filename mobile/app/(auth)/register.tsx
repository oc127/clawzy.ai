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

export default function RegisterScreen() {
  const { register } = useAuth();
  const { t } = useLanguage();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!name || !email || !password) return;
    if (password.length < 6) { setError("Password must be at least 6 characters"); return; }
    setError("");
    setLoading(true);
    try {
      await register(email, password, name);
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
        <View style={styles.header}>
          <Logo size="lg" />
        </View>

        <View style={styles.card}>
          <Text style={styles.title}>{t.auth.register.title}</Text>
          <Text style={styles.subtitle}>{t.auth.register.subtitle}</Text>

          {error ? (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : null}

          <View style={styles.form}>
            <Input
              label={t.auth.register.name}
              placeholder="Your name"
              value={name}
              onChangeText={setName}
              textContentType="name"
            />
            <Input
              label={t.auth.register.email}
              placeholder="you@example.com"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              textContentType="emailAddress"
            />
            <Input
              label={t.auth.register.password}
              placeholder="At least 6 characters"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              textContentType="newPassword"
            />
          </View>

          {/* Perks */}
          <View style={styles.perks}>
            {["500 free credits", "6+ AI models", "No credit card needed"].map((p) => (
              <View key={p} style={styles.perkRow}>
                <View style={styles.perkDot} />
                <Text style={styles.perkText}>{p}</Text>
              </View>
            ))}
          </View>

          <Button
            onPress={handleRegister}
            loading={loading}
            disabled={!name || !email || !password}
            size="lg"
            style={styles.submitBtn}
          >
            {t.auth.register.submit}
          </Button>

          <View style={styles.footer}>
            <Text style={styles.footerText}>{t.auth.register.haveAccount} </Text>
            <Link href="/(auth)/login" asChild>
              <TouchableOpacity>
                <Text style={styles.link}>{t.auth.register.login}</Text>
              </TouchableOpacity>
            </Link>
          </View>
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
    backgroundColor: "#FEF2F2",
    borderWidth: 1,
    borderColor: "#FECACA",
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  errorText: { ...typography.sm, color: colors.error },
  form: { gap: 16, marginBottom: 16 },
  perks: { gap: 6, marginBottom: 20 },
  perkRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  perkDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: colors.primary },
  perkText: { ...typography.sm, color: colors.textSecondary },
  submitBtn: { marginBottom: 16 },
  footer: { flexDirection: "row", justifyContent: "center", alignItems: "center" },
  footerText: { ...typography.sm, color: colors.textSecondary },
  link: { ...typography.sm, ...typography.bold, color: colors.primary },
});
