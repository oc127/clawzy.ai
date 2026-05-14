import React, { useEffect, useState, useCallback } from "react";
import {
  View, Text, ScrollView,
  RefreshControl, StyleSheet, ActivityIndicator,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useLanguage } from "@/context/LanguageContext";
import { getLucyState, type LucyState } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { colors, spacing, radius, typography } from "@/lib/theme";

function StatItem({ label, value, emoji }: { label: string; value: string; emoji: string }) {
  return (
    <View style={styles.statItem}>
      <Text style={styles.statEmoji}>{emoji}</Text>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function AffectionBar({ value }: { value: number }) {
  const percent = Math.min(100, Math.max(0, value));
  return (
    <View style={styles.barOuter}>
      <View style={[styles.barInner, { width: `${percent}%` }]} />
    </View>
  );
}

export default function StatusScreen() {
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();
  const [state, setState] = useState<LucyState | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const s = await getLucyState();
      setState(s);
    } catch {
      // ignore
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onRefresh = () => { setRefreshing(true); load(); };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
    >
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <Text style={styles.headerTitle}>{t.lucy.title}</Text>
      </View>

      {state ? (
        <>
          {/* Mood & Affection */}
          <Card style={styles.moodCard}>
            <View style={styles.moodHeader}>
              <Text style={styles.moodEmoji}>
                {state.mood === "happy" ? "😊" : state.mood === "excited" ? "🤩" : state.mood === "calm" ? "😌" : state.mood === "sad" ? "😢" : "😐"}
              </Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.moodLabel}>{t.lucy.mood}</Text>
                <Text style={styles.moodValue}>{state.mood}</Text>
              </View>
            </View>

            <Text style={styles.affectionLabel}>{t.lucy.affection}: {state.affection}%</Text>
            <AffectionBar value={state.affection} />
          </Card>

          {/* Stats Grid */}
          <View style={styles.statsRow}>
            <Card style={styles.statCard}>
              <StatItem
                label={t.lucy.stage}
                value={state.relationship_stage}
                emoji="💫"
              />
            </Card>
            <Card style={styles.statCard}>
              <StatItem
                label={t.lucy.streak}
                value={`${state.interaction_streak}`}
                emoji="🔥"
              />
            </Card>
          </View>

          <View style={styles.statsRow}>
            <Card style={styles.statCard}>
              <StatItem
                label={t.lucy.totalInteractions}
                value={`${state.total_interactions}`}
                emoji="💬"
              />
            </Card>
            <Card style={styles.statCard}>
              <StatItem
                label={t.lucy.model}
                value={state.preferred_model}
                emoji="🧠"
              />
            </Card>
          </View>

          {/* Personality */}
          <Card style={styles.personalityCard}>
            <Text style={styles.sectionTitle}>{t.lucy.personality}</Text>
            <View style={styles.personalityPill}>
              <Text style={styles.personalityText}>{state.personality_type}</Text>
            </View>
          </Card>

          {/* Expressions */}
          <Card style={styles.expressionsCard}>
            <Text style={styles.sectionTitle}>{t.lucy.expressions}</Text>
            {state.unlocked_expressions.length > 0 ? (
              <View style={styles.expressionGrid}>
                {state.unlocked_expressions.map((expr) => (
                  <View key={expr} style={styles.expressionPill}>
                    <Text style={styles.expressionText}>{expr}</Text>
                  </View>
                ))}
              </View>
            ) : (
              <Text style={styles.noExpressions}>{t.lucy.noExpressions}</Text>
            )}
          </Card>

          {/* Last interaction */}
          {state.last_interaction_at && (
            <View style={styles.lastInteraction}>
              <Text style={styles.lastInteractionText}>
                Last interaction: {new Date(state.last_interaction_at).toLocaleString()}
              </Text>
            </View>
          )}
        </>
      ) : (
        <View style={styles.empty}>
          <Text style={{ fontSize: 48 }}>💖</Text>
          <Text style={styles.emptyTitle}>{t.lucy.title}</Text>
          <Text style={styles.emptySubtitle}>{t.chat.noMessages}</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.backgroundSecondary },
  content: { paddingBottom: 32 },
  loadingContainer: { flex: 1, alignItems: "center", justifyContent: "center" },
  header: {
    backgroundColor: colors.white,
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.xl,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTitle: { ...typography.xl, ...typography.extrabold, color: colors.text },
  moodCard: {
    margin: spacing.xl,
    marginBottom: spacing.md,
    padding: spacing.lg,
  },
  moodHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  moodEmoji: { fontSize: 36 },
  moodLabel: { ...typography.sm, color: colors.textSecondary },
  moodValue: { ...typography.lg, ...typography.bold, color: colors.text, textTransform: "capitalize" },
  affectionLabel: { ...typography.sm, ...typography.semibold, color: colors.textSecondary, marginBottom: spacing.sm },
  barOuter: {
    height: 8,
    backgroundColor: colors.border,
    borderRadius: radius.full,
    overflow: "hidden",
  },
  barInner: {
    height: 8,
    backgroundColor: colors.primary,
    borderRadius: radius.full,
  },
  statsRow: {
    flexDirection: "row",
    gap: spacing.md,
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.md,
  },
  statCard: {
    flex: 1,
    alignItems: "center",
    padding: spacing.lg,
  },
  statItem: {
    alignItems: "center",
    gap: 4,
  },
  statEmoji: { fontSize: 24, marginBottom: 4 },
  statValue: { ...typography.md, ...typography.bold, color: colors.text },
  statLabel: { ...typography.xs, color: colors.textSecondary, textAlign: "center" },
  personalityCard: {
    marginHorizontal: spacing.xl,
    marginBottom: spacing.md,
    padding: spacing.lg,
  },
  sectionTitle: { ...typography.md, ...typography.bold, color: colors.text, marginBottom: spacing.md },
  personalityPill: {
    alignSelf: "flex-start",
    backgroundColor: colors.primaryLight,
    borderRadius: radius.full,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  personalityText: { ...typography.sm, ...typography.bold, color: colors.primary },
  expressionsCard: {
    marginHorizontal: spacing.xl,
    marginBottom: spacing.md,
    padding: spacing.lg,
  },
  expressionGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  expressionPill: {
    backgroundColor: colors.indigoLight,
    borderRadius: radius.full,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  expressionText: { ...typography.sm, color: colors.purple },
  noExpressions: { ...typography.sm, color: colors.textMuted },
  lastInteraction: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm,
  },
  lastInteractionText: { ...typography.xs, color: colors.textMuted, textAlign: "center" },
  empty: { alignItems: "center", gap: spacing.sm, paddingTop: spacing.xxxl * 2 },
  emptyTitle: { ...typography.lg, ...typography.bold, color: colors.text },
  emptySubtitle: { ...typography.base, color: colors.textSecondary, textAlign: "center" },
});
