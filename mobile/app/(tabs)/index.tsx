import React, { useEffect, useState, useCallback } from "react";
import {
  View, Text, ScrollView, TouchableOpacity,
  RefreshControl, StyleSheet, ActivityIndicator,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Link } from "expo-router";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { getAgents, type Agent } from "@/lib/api";
import { Logo } from "@/components/Logo";
import { Card } from "@/components/ui/Card";
import { colors, spacing, radius, typography, shadow } from "@/lib/theme";

function StatCard({ label, value, emoji, bg }: { label: string; value: string; emoji: string; bg: string }) {
  return (
    <Card style={[styles.statCard, { flex: 1 }]}>
      <View style={[styles.statIcon, { backgroundColor: bg }]}>
        <Text style={{ fontSize: 18 }}>{emoji}</Text>
      </View>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </Card>
  );
}

function AgentRow({ agent }: { agent: Agent }) {
  const statusColor = agent.status === "running" ? colors.success : agent.status === "error" ? colors.error : colors.textMuted;
  return (
    <Link href={`/agents/${agent.id}`} asChild>
      <TouchableOpacity style={styles.agentRow} activeOpacity={0.7}>
        <View style={styles.agentIcon}>
          <Text style={{ fontSize: 20 }}>🤖</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.agentName} numberOfLines={1}>{agent.name}</Text>
          <Text style={styles.agentModel} numberOfLines={1}>{agent.model_name}</Text>
        </View>
        <View style={styles.statusDot(statusColor)} />
      </TouchableOpacity>
    </Link>
  );
}

export default function DashboardScreen() {
  const insets = useSafeAreaInsets();
  const { user, refreshUser } = useAuth();
  const { t } = useLanguage();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [a] = await Promise.all([getAgents(), refreshUser()]);
      setAgents(a);
    } catch {
      // ignore
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [refreshUser]);

  useEffect(() => { load(); }, [load]);

  const onRefresh = () => { setRefreshing(true); load(); };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  const runningAgents = agents.filter((a) => a.status === "running").length;

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
    >
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <Logo size="sm" />
        <View style={styles.avatarCircle}>
          <Text style={styles.avatarText}>
            {user?.name?.charAt(0).toUpperCase() ?? "?"}
          </Text>
        </View>
      </View>

      {/* Welcome */}
      <View style={styles.welcomeSection}>
        <Text style={styles.welcomeLabel}>{t.dashboard.welcome},</Text>
        <Text style={styles.welcomeName}>{user?.name?.split(" ")[0] ?? ""} 👋</Text>
      </View>

      {/* Stat cards */}
      <View style={styles.statsRow}>
        <StatCard
          label={t.dashboard.credits}
          value={user?.credit_balance?.toLocaleString() ?? "0"}
          emoji="💳"
          bg={colors.primaryLight}
        />
        <StatCard
          label={t.dashboard.agents}
          value={`${runningAgents}/${agents.length}`}
          emoji="🤖"
          bg={colors.indigoLight}
        />
      </View>

      {/* My Agents */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>{t.tabs.agents}</Text>
          <Link href="/agents" asChild>
            <TouchableOpacity>
              <Text style={styles.seeAll}>{t.dashboard.seeAll}</Text>
            </TouchableOpacity>
          </Link>
        </View>

        {agents.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyEmoji}>🤖</Text>
            <Text style={styles.emptyTitle}>{t.agents.noAgents}</Text>
            <Text style={styles.emptySubtitle}>{t.agents.createFirst}</Text>
            <Link href="/agents" asChild>
              <TouchableOpacity style={styles.createBtn}>
                <Text style={styles.createBtnText}>+ {t.agents.newAgent}</Text>
              </TouchableOpacity>
            </Link>
          </View>
        ) : (
          <Card style={styles.agentsList}>
            {agents.slice(0, 3).map((agent, i) => (
              <View key={agent.id}>
                <AgentRow agent={agent} />
                {i < Math.min(agents.length, 3) - 1 && <View style={styles.divider} />}
              </View>
            ))}
          </Card>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.backgroundSecondary },
  content: { paddingBottom: 32 },
  loadingContainer: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: colors.background },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.lg,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  avatarCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarText: { color: colors.white, ...typography.base, ...typography.bold },
  welcomeSection: {
    backgroundColor: colors.white,
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.xl,
  },
  welcomeLabel: { ...typography.base, color: colors.textSecondary },
  welcomeName: { ...typography.xxl, ...typography.extrabold, color: colors.text },
  statsRow: {
    flexDirection: "row",
    gap: spacing.md,
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.xl,
    paddingBottom: spacing.md,
  },
  statCard: { gap: 4, alignItems: "flex-start" },
  statIcon: {
    width: 44,
    height: 44,
    borderRadius: radius.lg,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },
  statValue: { ...typography.xl, ...typography.extrabold, color: colors.text },
  statLabel: { ...typography.xs, color: colors.textSecondary },
  section: { paddingHorizontal: spacing.xl, marginTop: spacing.sm },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.md,
  },
  sectionTitle: { ...typography.lg, ...typography.bold, color: colors.text },
  seeAll: { ...typography.sm, color: colors.primary, ...typography.semibold },
  emptyCard: {
    backgroundColor: colors.white,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.xxl,
    alignItems: "center",
    gap: spacing.sm,
  },
  emptyEmoji: { fontSize: 36, marginBottom: 4 },
  emptyTitle: { ...typography.md, ...typography.bold, color: colors.text },
  emptySubtitle: { ...typography.sm, color: colors.textSecondary, textAlign: "center" },
  createBtn: {
    marginTop: 4,
    backgroundColor: colors.primaryLight,
    borderRadius: radius.full,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.sm,
  },
  createBtnText: { ...typography.sm, ...typography.bold, color: colors.primary },
  agentsList: { padding: 0, overflow: "hidden" },
  agentRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    padding: spacing.lg,
  },
  agentIcon: {
    width: 40,
    height: 40,
    borderRadius: radius.lg,
    backgroundColor: colors.indigoLight,
    alignItems: "center",
    justifyContent: "center",
  },
  agentName: { ...typography.base, ...typography.semibold, color: colors.text },
  agentModel: { ...typography.xs, color: colors.textMuted, marginTop: 2 },
  statusDot: (color: string) => ({
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: color,
  }),
  divider: { height: 1, backgroundColor: colors.border, marginHorizontal: spacing.lg },
});
