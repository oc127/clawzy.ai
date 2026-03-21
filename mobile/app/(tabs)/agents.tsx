import React, { useEffect, useState, useCallback } from "react";
import {
  View, Text, ScrollView, TouchableOpacity, Modal,
  RefreshControl, StyleSheet, Alert, ActivityIndicator,
} from "react-native";
import { Link } from "expo-router";
import { useLanguage } from "@/context/LanguageContext";
import { getAgents, createAgent, deleteAgent, getModels, type Agent, type Model } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { colors, spacing, radius, typography } from "@/lib/theme";

function AgentCard({ agent, onDelete }: { agent: Agent; onDelete: () => void }) {
  const { t } = useLanguage();
  const statusColors: Record<string, string> = {
    running: colors.success,
    stopped: colors.textMuted,
    error: colors.error,
  };
  const statusLabels: Record<string, string> = {
    running: t.agents.running,
    stopped: t.agents.stopped,
    error: t.agents.error,
  };

  const confirmDelete = () => {
    Alert.alert(t.agents.delete, `Delete "${agent.name}"?`, [
      { text: t.common.cancel, style: "cancel" },
      { text: t.common.delete, style: "destructive", onPress: onDelete },
    ]);
  };

  return (
    <Card style={styles.agentCard}>
      <Link href={`/agents/${agent.id}`} asChild>
        <TouchableOpacity activeOpacity={0.8} style={styles.agentCardInner}>
          <View style={styles.agentCardHeader}>
            <View style={styles.agentIconBig}>
              <Text style={{ fontSize: 24 }}>🤖</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.agentName} numberOfLines={1}>{agent.name}</Text>
              <Text style={styles.agentModel} numberOfLines={1}>{agent.model}</Text>
            </View>
            <View style={styles.statusPill(statusColors[agent.status])}>
              <View style={styles.statusDot(statusColors[agent.status])} />
              <Text style={styles.statusText(statusColors[agent.status])}>
                {statusLabels[agent.status]}
              </Text>
            </View>
          </View>
          {agent.description ? (
            <Text style={styles.agentDesc} numberOfLines={2}>{agent.description}</Text>
          ) : null}
        </TouchableOpacity>
      </Link>
      <TouchableOpacity style={styles.deleteBtn} onPress={confirmDelete}>
        <Text style={styles.deleteBtnText}>🗑</Text>
      </TouchableOpacity>
    </Card>
  );
}

export default function AgentsScreen() {
  const { t } = useLanguage();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", model: "" });

  const load = useCallback(async () => {
    try {
      const [a, m] = await Promise.all([getAgents(), getModels()]);
      setAgents(a);
      setModels(m);
      if (m.length > 0 && !form.model) setForm((f) => ({ ...f, model: m[0].id }));
    } catch {
      // ignore
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!form.name || !form.model) return;
    setCreating(true);
    try {
      const agent = await createAgent({ name: form.name, description: form.description, model: form.model });
      setAgents((prev) => [agent, ...prev]);
      setModalVisible(false);
      setForm({ name: "", description: "", model: models[0]?.id ?? "" });
    } catch {
      Alert.alert(t.common.error);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteAgent(id);
      setAgents((prev) => prev.filter((a) => a.id !== id));
    } catch {
      Alert.alert(t.common.error);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>{t.agents.title}</Text>
        <TouchableOpacity style={styles.addBtn} onPress={() => setModalVisible(true)}>
          <Text style={styles.addBtnText}>+ {t.agents.newAgent}</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={colors.primary} />}
      >
        {agents.length === 0 ? (
          <View style={styles.empty}>
            <Text style={{ fontSize: 48 }}>🤖</Text>
            <Text style={styles.emptyTitle}>{t.agents.noAgents}</Text>
            <Text style={styles.emptySubtitle}>{t.agents.createFirst}</Text>
            <Button onPress={() => setModalVisible(true)} style={{ marginTop: 8 }}>
              {t.agents.newAgent}
            </Button>
          </View>
        ) : (
          agents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onDelete={() => handleDelete(agent.id)}
            />
          ))
        )}
      </ScrollView>

      {/* Create Agent Modal */}
      <Modal visible={modalVisible} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modal}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setModalVisible(false)}>
              <Text style={styles.modalCancel}>{t.common.cancel}</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>{t.agents.newAgent}</Text>
            <View style={{ width: 60 }} />
          </View>

          <ScrollView contentContainerStyle={styles.modalContent}>
            <Input
              label={t.agents.name}
              placeholder="My Coding Assistant"
              value={form.name}
              onChangeText={(v) => setForm((f) => ({ ...f, name: v }))}
            />
            <Input
              label={t.agents.description}
              placeholder="What does this agent do?"
              value={form.description}
              onChangeText={(v) => setForm((f) => ({ ...f, description: v }))}
              multiline
              numberOfLines={3}
              style={{ height: 80, textAlignVertical: "top", paddingTop: 12 }}
            />

            {/* Model selector */}
            <Text style={styles.fieldLabel}>{t.agents.model}</Text>
            <View style={styles.modelGrid}>
              {models.slice(0, 6).map((m) => (
                <TouchableOpacity
                  key={m.id}
                  style={[styles.modelPill, form.model === m.id && styles.modelPillActive]}
                  onPress={() => setForm((f) => ({ ...f, model: m.id }))}
                >
                  <Text style={[styles.modelPillText, form.model === m.id && styles.modelPillTextActive]}>
                    {m.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Button
              onPress={handleCreate}
              loading={creating}
              disabled={!form.name || !form.model}
              size="lg"
              style={{ marginTop: 8 }}
            >
              {t.agents.create}
            </Button>
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.backgroundSecondary },
  loadingContainer: { flex: 1, alignItems: "center", justifyContent: "center" },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.xl,
    paddingTop: 60,
    paddingBottom: spacing.lg,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTitle: { ...typography.xl, ...typography.extrabold, color: colors.text },
  addBtn: {
    backgroundColor: colors.primary,
    borderRadius: radius.full,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  addBtnText: { ...typography.sm, ...typography.bold, color: colors.white },
  content: { padding: spacing.xl, gap: spacing.md },
  empty: { alignItems: "center", gap: spacing.sm, paddingTop: 60 },
  emptyTitle: { ...typography.lg, ...typography.bold, color: colors.text },
  emptySubtitle: { ...typography.base, color: colors.textSecondary, textAlign: "center" },
  agentCard: { gap: 0, padding: 0, overflow: "hidden" },
  agentCardInner: { padding: spacing.lg },
  agentCardHeader: { flexDirection: "row", alignItems: "center", gap: spacing.md, marginBottom: 8 },
  agentIconBig: {
    width: 48, height: 48, borderRadius: radius.lg,
    backgroundColor: "#EEF2FF", alignItems: "center", justifyContent: "center",
  },
  agentName: { ...typography.md, ...typography.bold, color: colors.text },
  agentModel: { ...typography.xs, color: colors.textMuted, marginTop: 2 },
  agentDesc: { ...typography.sm, color: colors.textSecondary, lineHeight: 20 },
  statusPill: (color: string) => ({
    flexDirection: "row" as const,
    alignItems: "center" as const,
    gap: 4,
    backgroundColor: `${color}18`,
    borderRadius: radius.full,
    paddingHorizontal: 8,
    paddingVertical: 3,
  }),
  statusDot: (color: string) => ({ width: 5, height: 5, borderRadius: 3, backgroundColor: color }),
  statusText: (color: string) => ({ fontSize: 11, fontWeight: "600" as const, color }),
  deleteBtn: {
    borderTopWidth: 1, borderTopColor: colors.border,
    paddingVertical: spacing.md, alignItems: "center",
  },
  deleteBtnText: { fontSize: 18 },
  modal: { flex: 1, backgroundColor: colors.white },
  modalHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.xl,
    paddingTop: 60,
    paddingBottom: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  modalCancel: { ...typography.base, color: colors.primary },
  modalTitle: { ...typography.md, ...typography.bold, color: colors.text },
  modalContent: { padding: spacing.xl, gap: spacing.lg },
  fieldLabel: { ...typography.sm, ...typography.bold, color: colors.text },
  modelGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  modelPill: {
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
    borderRadius: radius.full, borderWidth: 1.5, borderColor: colors.border,
  },
  modelPillActive: { borderColor: colors.primary, backgroundColor: colors.primaryLight },
  modelPillText: { ...typography.sm, color: colors.textSecondary },
  modelPillTextActive: { color: colors.primary, ...typography.bold },
});
