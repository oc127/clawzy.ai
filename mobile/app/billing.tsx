import React, { useEffect, useState, useCallback } from "react";
import {
  View, Text, ScrollView, TouchableOpacity,
  StyleSheet, ActivityIndicator, RefreshControl,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { router } from "expo-router";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { apiGet, type CreditTransaction } from "@/lib/api";
import { colors, spacing, radius, typography } from "@/lib/theme";

interface Credits {
  balance: number;
  used_this_period: number;
  plan: string;
}

export default function BillingScreen() {
  const insets = useSafeAreaInsets();
  const { user } = useAuth();
  const { t } = useLanguage();
  const [credits, setCredits] = useState<Credits | null>(null);
  const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [c, txns] = await Promise.all([
        apiGet<Credits>("/billing/credits"),
        apiGet<CreditTransaction[]>("/billing/credits/transactions"),
      ]);
      setCredits(c);
      setTransactions(txns);
    } catch {
      // ignore
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const typeIcons: Record<string, string> = {
    usage: "📉",
    purchase: "💰",
    bonus: "🎁",
  };

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
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={colors.primary} />}
    >
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <TouchableOpacity
          onPress={() => { if (router.canGoBack()) router.back(); else router.replace("/(tabs)/settings"); }}
          hitSlop={{ top: 12, bottom: 12, left: 8, right: 8 }}
        >
          <Text style={styles.backText}>← {t.common.back}</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t.settings.billing}</Text>
      </View>

      {/* Overview Cards */}
      <View style={styles.cardRow}>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>{t.settings.credits}</Text>
          <Text style={styles.statValue}>{credits?.balance?.toLocaleString() ?? user?.credit_balance?.toLocaleString() ?? "0"}</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>{t.settings.plan}</Text>
          <Text style={[styles.statValue, { color: colors.primary }]}>{(credits?.plan ?? user?.plan ?? "free").toUpperCase()}</Text>
        </View>
      </View>

      {/* Transactions */}
      <View style={styles.txnSection}>
        <Text style={styles.txnTitle}>{t.settings.transactions}</Text>
        {transactions.length === 0 ? (
          <View style={styles.emptyTxn}>
            <Text style={styles.emptyTxnText}>{t.settings.noTransactions}</Text>
          </View>
        ) : (
          transactions.map((txn) => (
            <View key={txn.id} style={styles.txnRow}>
              <Text style={styles.txnIcon}>{typeIcons[txn.type] ?? "📋"}</Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.txnDesc} numberOfLines={1}>{txn.description}</Text>
                <Text style={styles.txnDate}>{new Date(txn.created_at).toLocaleDateString()}</Text>
              </View>
              <Text style={[styles.txnAmount, txn.amount > 0 ? styles.txnPositive : styles.txnNegative]}>
                {txn.amount > 0 ? "+" : ""}{txn.amount}
              </Text>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.backgroundSecondary },
  content: { paddingBottom: 48 },
  loadingContainer: { flex: 1, alignItems: "center", justifyContent: "center" },
  header: {
    backgroundColor: colors.white,
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    gap: spacing.sm,
  },
  backText: { ...typography.base, color: colors.primary, fontWeight: "600" },
  headerTitle: { ...typography.xl, ...typography.extrabold, color: colors.text },
  cardRow: {
    flexDirection: "row",
    gap: spacing.md,
    padding: spacing.xl,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.white,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    alignItems: "center",
    gap: spacing.xs,
  },
  statLabel: { ...typography.xs, color: colors.textMuted, textTransform: "uppercase" },
  statValue: { ...typography.xl, ...typography.extrabold, color: colors.text },
  txnSection: {
    paddingHorizontal: spacing.xl,
  },
  txnTitle: { ...typography.lg, ...typography.bold, color: colors.text, marginBottom: spacing.md },
  emptyTxn: {
    backgroundColor: colors.white,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.xxl,
    alignItems: "center",
  },
  emptyTxnText: { ...typography.base, color: colors.textSecondary },
  txnRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    backgroundColor: colors.white,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  txnIcon: { fontSize: 20 },
  txnDesc: { ...typography.sm, color: colors.text },
  txnDate: { ...typography.xs, color: colors.textMuted, marginTop: 2 },
  txnAmount: { ...typography.md, ...typography.bold },
  txnPositive: { color: colors.success },
  txnNegative: { color: colors.error },
});
