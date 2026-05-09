import React, { useEffect, useState, useCallback } from "react";
import {
  View, Text, ScrollView, TouchableOpacity,
  RefreshControl, StyleSheet, ActivityIndicator,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useLanguage } from "@/context/LanguageContext";
import { getConversations, type Conversation } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { colors, spacing, radius, typography } from "@/lib/theme";

export default function MemoryScreen() {
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const convs = await getConversations();
      setConversations(convs);
    } catch {
      // ignore
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

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
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <Text style={styles.headerTitle}>{t.memory.title}</Text>
        <Text style={styles.headerSubtitle}>{t.memory.subtitle}</Text>
      </View>

      {conversations.length === 0 ? (
        <View style={styles.empty}>
          <Text style={{ fontSize: 48 }}>📝</Text>
          <Text style={styles.emptyTitle}>{t.memory.noConversations}</Text>
          <Text style={styles.emptySubtitle}>{t.memory.startFirst}</Text>
        </View>
      ) : (
        <View style={styles.list}>
          {conversations.map((conv) => (
            <Card key={conv.id} style={styles.convCard}>
              <View style={styles.convRow}>
                <View style={styles.convIcon}>
                  <Text style={{ fontSize: 16 }}>💬</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.convTitle} numberOfLines={1}>
                    {conv.title || `Chat ${conv.id.slice(0, 8)}`}
                  </Text>
                  <Text style={styles.convDate}>
                    {new Date(conv.updated_at).toLocaleDateString()} {new Date(conv.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </Text>
                </View>
              </View>
            </Card>
          ))}
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
  headerSubtitle: { ...typography.base, color: colors.textSecondary, marginTop: 2 },
  empty: {
    alignItems: "center",
    gap: spacing.sm,
    paddingTop: spacing.xxxl * 2,
    paddingHorizontal: spacing.xl,
  },
  emptyTitle: { ...typography.lg, ...typography.bold, color: colors.text },
  emptySubtitle: { ...typography.base, color: colors.textSecondary, textAlign: "center" },
  list: {
    padding: spacing.xl,
    gap: spacing.md,
  },
  convCard: {
    padding: spacing.lg,
  },
  convRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
  },
  convIcon: {
    width: 40,
    height: 40,
    borderRadius: radius.lg,
    backgroundColor: colors.primaryLight,
    alignItems: "center",
    justifyContent: "center",
  },
  convTitle: { ...typography.base, ...typography.semibold, color: colors.text },
  convDate: { ...typography.xs, color: colors.textMuted, marginTop: 2 },
});
