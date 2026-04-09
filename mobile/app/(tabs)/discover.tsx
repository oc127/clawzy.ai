import React from "react";
import { View, Text, ScrollView, StyleSheet } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useLanguage } from "@/context/LanguageContext";
import { colors, spacing, radius, typography } from "@/lib/theme";
import { Card } from "@/components/ui/Card";

/** 与后端实际接入的模型一致：DeepSeek + 千问（Qwen） */
const MODELS = [
  { name: "DeepSeek V3", id: "deepseek-chat", provider: "DeepSeek", emoji: "🔵", badge: "Standard", badgeColor: colors.success },
  { name: "DeepSeek R1", id: "deepseek-reasoner", provider: "DeepSeek", emoji: "🔷", badge: "Premium", badgeColor: colors.primary },
  { name: "Qwen Turbo", id: "qwen-turbo", provider: "Alibaba", emoji: "🟠", badge: "Standard", badgeColor: colors.success },
  { name: "Qwen Plus", id: "qwen-plus", provider: "Alibaba", emoji: "🟡", badge: "Standard", badgeColor: colors.warning },
  { name: "Qwen Max", id: "qwen-max", provider: "Alibaba", emoji: "🔴", badge: "Standard", badgeColor: colors.primary },
];

export default function DiscoverScreen() {
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <Text style={styles.headerTitle}>{t.tabs.discover}</Text>
        <Text style={styles.headerSubtitle}>{t.discover.subtitle}</Text>
      </View>

      {/* Models section */}
      <Text style={styles.sectionTitle}>{t.discover.availableModels}</Text>
      <View style={styles.modelGrid}>
        {MODELS.map((m) => (
          <Card key={m.id} style={styles.modelCard}>
            <Text style={{ fontSize: 28, marginBottom: 8 }}>{m.emoji}</Text>
            <Text style={styles.modelName} numberOfLines={1}>{m.name}</Text>
            <Text style={styles.modelProvider}>{m.provider}</Text>
            <View style={[styles.badge, { backgroundColor: `${m.badgeColor}18` }]}>
              <Text style={[styles.badgeText, { color: m.badgeColor }]}>{m.badge}</Text>
            </View>
          </Card>
        ))}
      </View>

      {/* Coming soon */}
      <View style={styles.comingSoon}>
        <Text style={{ fontSize: 32 }}>🦞</Text>
        <Text style={styles.comingSoonTitle}>{t.discover.comingSoonTitle}</Text>
        <Text style={styles.comingSoonSubtitle}>{t.discover.comingSoonSubtitle}</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.backgroundSecondary },
  content: { paddingBottom: 32 },
  header: {
    backgroundColor: colors.white,
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.xl,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTitle: { ...typography.xl, ...typography.extrabold, color: colors.text },
  headerSubtitle: { ...typography.base, color: colors.textSecondary, marginTop: 2 },
  sectionTitle: {
    ...typography.lg, ...typography.bold, color: colors.text,
    paddingHorizontal: spacing.xl, paddingTop: spacing.xl, paddingBottom: spacing.md,
  },
  modelGrid: {
    flexDirection: "row", flexWrap: "wrap", gap: spacing.md,
    paddingHorizontal: spacing.xl,
  },
  modelCard: {
    width: "47%", alignItems: "flex-start", padding: spacing.lg,
  },
  modelName: { ...typography.sm, ...typography.bold, color: colors.text, marginBottom: 2 },
  modelProvider: { ...typography.xs, color: colors.textMuted, marginBottom: 8 },
  badge: {
    borderRadius: radius.full, paddingHorizontal: 8, paddingVertical: 2,
  },
  badgeText: { fontSize: 11, fontWeight: "700" },
  comingSoon: {
    margin: spacing.xl, padding: spacing.xxl,
    backgroundColor: colors.white, borderRadius: radius.xl,
    borderWidth: 1, borderColor: colors.border,
    alignItems: "center", gap: spacing.sm,
  },
  comingSoonTitle: { ...typography.md, ...typography.bold, color: colors.text },
  comingSoonSubtitle: { ...typography.sm, color: colors.textSecondary },
});
