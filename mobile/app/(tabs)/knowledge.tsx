import React, { useEffect, useState, useCallback } from "react";
import {
  View, Text, ScrollView, TouchableOpacity,
  RefreshControl, StyleSheet, ActivityIndicator,
  Alert, TextInput,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useLanguage } from "@/context/LanguageContext";
import {
  getKnowledgeBases, createKnowledgeBase, deleteKnowledgeBase,
  getKnowledgeDocuments, deleteKnowledgeDocument,
  type KnowledgeBase, type KnowledgeDocument,
} from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { colors, spacing, radius, typography } from "@/lib/theme";

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function StatusBadge({ status, t }: { status: string; t: any }) {
  const statusConfig: Record<string, { bg: string; color: string; label: string }> = {
    pending: { bg: "#FEF3C7", color: "#D97706", label: t.knowledge.pending },
    processing: { bg: "#DBEAFE", color: "#2563EB", label: t.knowledge.processing },
    ready: { bg: "#D1FAE5", color: "#059669", label: t.knowledge.ready },
    failed: { bg: "#FEE2E2", color: "#DC2626", label: t.knowledge.failed },
  };
  const config = statusConfig[status] ?? statusConfig.pending;
  return (
    <View style={[styles.badge, { backgroundColor: config.bg }]}>
      <Text style={[styles.badgeText, { color: config.color }]}>{config.label}</Text>
    </View>
  );
}

function ActiveBadge({ active, t }: { active: boolean; t: any }) {
  return (
    <View style={[styles.badge, { backgroundColor: active ? "#D1FAE5" : "#F3F4F6" }]}>
      <Text style={[styles.badgeText, { color: active ? "#059669" : "#6B7280" }]}>
        {active ? t.knowledge.active : t.knowledge.inactive}
      </Text>
    </View>
  );
}

function FileTypeBadge({ fileType }: { fileType: string }) {
  return (
    <View style={[styles.badge, { backgroundColor: colors.indigoLight }]}>
      <Text style={[styles.badgeText, { color: colors.purple }]}>{fileType.toUpperCase()}</Text>
    </View>
  );
}

export default function KnowledgeScreen() {
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<Record<string, KnowledgeDocument[]>>({});
  const [loadingDocs, setLoadingDocs] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    try {
      const kbs = await getKnowledgeBases();
      setKnowledgeBases(kbs);
    } catch {
      // ignore
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleExpand = useCallback(async (kbId: string) => {
    if (expandedId === kbId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(kbId);
    if (!documents[kbId]) {
      setLoadingDocs(kbId);
      try {
        const docs = await getKnowledgeDocuments(kbId);
        setDocuments((prev: Record<string, KnowledgeDocument[]>) => ({ ...prev, [kbId]: docs }));
      } catch {
        // ignore
      } finally {
        setLoadingDocs(null);
      }
    }
  }, [expandedId, documents]);

  const handleCreate = useCallback(async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const kb = await createKnowledgeBase({
        name: newName.trim(),
        description: newDescription.trim() || undefined,
      });
      setKnowledgeBases((prev: KnowledgeBase[]) => [kb, ...prev]);
      setNewName("");
      setNewDescription("");
      setShowCreate(false);
    } catch {
      Alert.alert(t.common.error);
    } finally {
      setCreating(false);
    }
  }, [newName, newDescription, t]);

  const handleDeleteKb = useCallback((kb: KnowledgeBase) => {
    Alert.alert(
      t.knowledge.deleteKb,
      t.knowledge.deleteKbConfirm,
      [
        { text: t.common.cancel, style: "cancel" },
        {
          text: t.common.delete,
          style: "destructive",
          onPress: async () => {
            try {
              await deleteKnowledgeBase(kb.id);
              setKnowledgeBases((prev: KnowledgeBase[]) => prev.filter((k: KnowledgeBase) => k.id !== kb.id));
              if (expandedId === kb.id) setExpandedId(null);
            } catch {
              Alert.alert(t.common.error);
            }
          },
        },
      ],
    );
  }, [t, expandedId]);

  const handleDeleteDoc = useCallback((kbId: string, doc: KnowledgeDocument) => {
    Alert.alert(
      t.knowledge.deleteDoc,
      t.knowledge.deleteDocConfirm,
      [
        { text: t.common.cancel, style: "cancel" },
        {
          text: t.common.delete,
          style: "destructive",
          onPress: async () => {
            try {
              await deleteKnowledgeDocument(kbId, doc.id);
              setDocuments((prev: Record<string, KnowledgeDocument[]>) => ({
                ...prev,
                [kbId]: (prev[kbId] ?? []).filter((d: KnowledgeDocument) => d.id !== doc.id),
              }));
              // Update document_count in the KB list
              setKnowledgeBases((prev: KnowledgeBase[]) =>
                prev.map((kb: KnowledgeBase) =>
                  kb.id === kbId ? { ...kb, document_count: Math.max(0, kb.document_count - 1) } : kb,
                ),
              );
            } catch {
              Alert.alert(t.common.error);
            }
          },
        },
      ],
    );
  }, [t]);

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
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => { setRefreshing(true); load(); }}
          tintColor={colors.primary}
        />
      }
    >
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <Text style={styles.headerTitle}>{t.knowledge.title}</Text>
        <Text style={styles.headerSubtitle}>{t.knowledge.subtitle}</Text>
      </View>

      {/* Create New Button / Form */}
      <View style={styles.createSection}>
        {showCreate ? (
          <Card style={styles.createCard}>
            <Text style={styles.createCardTitle}>{t.knowledge.createTitle}</Text>
            <TextInput
              style={styles.input}
              placeholder={t.knowledge.namePlaceholder}
              placeholderTextColor={colors.textMuted}
              value={newName}
              onChangeText={setNewName}
              autoFocus
            />
            <TextInput
              style={[styles.input, { marginTop: spacing.sm }]}
              placeholder={t.knowledge.subtitle}
              placeholderTextColor={colors.textMuted}
              value={newDescription}
              onChangeText={setNewDescription}
            />
            <View style={styles.createActions}>
              <TouchableOpacity
                style={styles.cancelBtn}
                onPress={() => { setShowCreate(false); setNewName(""); setNewDescription(""); }}
              >
                <Text style={styles.cancelBtnText}>{t.common.cancel}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.createBtn, !newName.trim() && styles.createBtnDisabled]}
                onPress={handleCreate}
                disabled={!newName.trim() || creating}
              >
                {creating ? (
                  <ActivityIndicator size="small" color={colors.white} />
                ) : (
                  <Text style={styles.createBtnText}>{t.common.save}</Text>
                )}
              </TouchableOpacity>
            </View>
          </Card>
        ) : (
          <TouchableOpacity style={styles.newBtn} onPress={() => setShowCreate(true)}>
            <Text style={styles.newBtnIcon}>+</Text>
            <Text style={styles.newBtnText}>{t.knowledge.createNew}</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Knowledge Base List */}
      {knowledgeBases.length === 0 ? (
        <View style={styles.empty}>
          <Text style={{ fontSize: 48 }}>📚</Text>
          <Text style={styles.emptyTitle}>{t.knowledge.empty}</Text>
          <Text style={styles.emptySubtitle}>{t.knowledge.emptySubtitle}</Text>
        </View>
      ) : (
        <View style={styles.list}>
          {knowledgeBases.map((kb: KnowledgeBase) => {
            const isExpanded = expandedId === kb.id;
            const kbDocs = documents[kb.id];
            return (
              <Card key={kb.id} style={styles.kbCard}>
                <TouchableOpacity
                  activeOpacity={0.7}
                  onPress={() => handleExpand(kb.id)}
                >
                  <View style={styles.kbHeader}>
                    <View style={styles.kbIcon}>
                      <Text style={{ fontSize: 16 }}>📚</Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <View style={styles.kbTitleRow}>
                        <Text style={styles.kbName} numberOfLines={1}>{kb.name}</Text>
                        <ActiveBadge active={kb.is_active} t={t} />
                      </View>
                      {kb.description ? (
                        <Text style={styles.kbDescription} numberOfLines={2}>{kb.description}</Text>
                      ) : null}
                    </View>
                    <Text style={styles.expandArrow}>{isExpanded ? "▲" : "▼"}</Text>
                  </View>

                  {/* Stats row */}
                  <View style={styles.kbStats}>
                    <View style={styles.kbStat}>
                      <Text style={styles.kbStatValue}>{kb.document_count}</Text>
                      <Text style={styles.kbStatLabel}>{t.knowledge.documents}</Text>
                    </View>
                    <View style={styles.kbStatDivider} />
                    <View style={styles.kbStat}>
                      <Text style={styles.kbStatValue}>{kb.total_chunks}</Text>
                      <Text style={styles.kbStatLabel}>{t.knowledge.chunks}</Text>
                    </View>
                    <View style={styles.kbStatDivider} />
                    <View style={styles.kbStat}>
                      <Text style={styles.kbStatValue}>
                        {new Date(kb.created_at).toLocaleDateString()}
                      </Text>
                      <Text style={styles.kbStatLabel}>Created</Text>
                    </View>
                  </View>
                </TouchableOpacity>

                {/* Expanded: Documents */}
                {isExpanded && (
                  <View style={styles.docsSection}>
                    <View style={styles.docsDivider} />
                    {loadingDocs === kb.id ? (
                      <ActivityIndicator
                        size="small"
                        color={colors.primary}
                        style={{ marginVertical: spacing.md }}
                      />
                    ) : kbDocs && kbDocs.length > 0 ? (
                      kbDocs.map((doc: KnowledgeDocument) => (
                        <View key={doc.id} style={styles.docRow}>
                          <View style={{ flex: 1 }}>
                            <Text style={styles.docFilename} numberOfLines={1}>
                              {doc.filename}
                            </Text>
                            <View style={styles.docMeta}>
                              <FileTypeBadge fileType={doc.file_type} />
                              <StatusBadge status={doc.status} t={t} />
                              <Text style={styles.docSize}>
                                {formatFileSize(doc.file_size)}
                              </Text>
                              {doc.chunk_count > 0 && (
                                <Text style={styles.docSize}>
                                  {doc.chunk_count} {t.knowledge.chunks}
                                </Text>
                              )}
                            </View>
                            {doc.error ? (
                              <Text style={styles.docError} numberOfLines={2}>
                                {doc.error}
                              </Text>
                            ) : null}
                          </View>
                          <TouchableOpacity
                            style={styles.deleteDocBtn}
                            onPress={() => handleDeleteDoc(kb.id, doc)}
                          >
                            <Text style={styles.deleteIcon}>✕</Text>
                          </TouchableOpacity>
                        </View>
                      ))
                    ) : (
                      <Text style={styles.noDocuments}>{t.knowledge.noDocuments}</Text>
                    )}

                    {/* Delete KB */}
                    <TouchableOpacity
                      style={styles.deleteKbBtn}
                      onPress={() => handleDeleteKb(kb)}
                    >
                      <Text style={styles.deleteKbBtnText}>{t.knowledge.deleteKb}</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </Card>
            );
          })}
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

  // Create section
  createSection: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.lg,
  },
  newBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.primary,
    borderRadius: radius.lg,
    paddingVertical: spacing.md,
    gap: spacing.sm,
  },
  newBtnIcon: {
    ...typography.lg,
    ...typography.bold,
    color: colors.white,
  },
  newBtnText: {
    ...typography.base,
    ...typography.semibold,
    color: colors.white,
  },
  createCard: {
    padding: spacing.lg,
  },
  createCardTitle: {
    ...typography.md,
    ...typography.bold,
    color: colors.text,
    marginBottom: spacing.md,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.borderInput,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    ...typography.base,
    color: colors.text,
  },
  createActions: {
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: spacing.sm,
    marginTop: spacing.lg,
  },
  cancelBtn: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cancelBtnText: {
    ...typography.sm,
    ...typography.semibold,
    color: colors.textSecondary,
  },
  createBtn: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: radius.sm,
    backgroundColor: colors.primary,
  },
  createBtnDisabled: {
    opacity: 0.5,
  },
  createBtnText: {
    ...typography.sm,
    ...typography.semibold,
    color: colors.white,
  },

  // Empty state
  empty: {
    alignItems: "center",
    gap: spacing.sm,
    paddingTop: spacing.xxxl * 2,
    paddingHorizontal: spacing.xl,
  },
  emptyTitle: { ...typography.lg, ...typography.bold, color: colors.text },
  emptySubtitle: { ...typography.base, color: colors.textSecondary, textAlign: "center" },

  // List
  list: {
    padding: spacing.xl,
    paddingTop: spacing.md,
    gap: spacing.md,
  },
  kbCard: {
    padding: spacing.lg,
  },

  // KB Header
  kbHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
  },
  kbIcon: {
    width: 40,
    height: 40,
    borderRadius: radius.lg,
    backgroundColor: colors.primaryLight,
    alignItems: "center",
    justifyContent: "center",
  },
  kbTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  kbName: {
    ...typography.base,
    ...typography.semibold,
    color: colors.text,
    flexShrink: 1,
  },
  kbDescription: {
    ...typography.sm,
    color: colors.textSecondary,
    marginTop: 2,
  },
  expandArrow: {
    ...typography.xs,
    color: colors.textMuted,
    marginLeft: spacing.sm,
  },

  // KB Stats
  kbStats: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: spacing.md,
    paddingTop: spacing.sm,
  },
  kbStat: {
    flex: 1,
    alignItems: "center",
  },
  kbStatValue: {
    ...typography.sm,
    ...typography.bold,
    color: colors.text,
  },
  kbStatLabel: {
    ...typography.xs,
    color: colors.textMuted,
    marginTop: 2,
  },
  kbStatDivider: {
    width: 1,
    height: 24,
    backgroundColor: colors.border,
  },

  // Badges
  badge: {
    borderRadius: radius.full,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
  },
  badgeText: {
    ...typography.xs,
    ...typography.semibold,
  },

  // Documents section
  docsSection: {
    marginTop: spacing.sm,
  },
  docsDivider: {
    height: 1,
    backgroundColor: colors.border,
    marginVertical: spacing.md,
  },
  docRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: spacing.sm,
    gap: spacing.sm,
  },
  docFilename: {
    ...typography.sm,
    ...typography.semibold,
    color: colors.text,
  },
  docMeta: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    marginTop: spacing.xs,
    flexWrap: "wrap",
  },
  docSize: {
    ...typography.xs,
    color: colors.textMuted,
  },
  docError: {
    ...typography.xs,
    color: colors.error,
    marginTop: spacing.xs,
  },
  deleteDocBtn: {
    width: 28,
    height: 28,
    borderRadius: radius.full,
    backgroundColor: colors.errorLight,
    alignItems: "center",
    justifyContent: "center",
  },
  deleteIcon: {
    ...typography.xs,
    color: colors.error,
  },
  noDocuments: {
    ...typography.sm,
    color: colors.textMuted,
    textAlign: "center",
    paddingVertical: spacing.md,
  },

  // Delete KB button
  deleteKbBtn: {
    marginTop: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.errorBorder,
    backgroundColor: colors.errorLight,
    alignItems: "center",
  },
  deleteKbBtnText: {
    ...typography.sm,
    ...typography.semibold,
    color: colors.error,
  },
});
