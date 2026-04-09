import React, { useState } from "react";
import {
  View, Text, ScrollView, TouchableOpacity,
  Modal, StyleSheet, Alert,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/context/AuthContext";
import { useLanguage, type Locale } from "@/context/LanguageContext";
import { colors, spacing, radius, typography } from "@/lib/theme";

function SettingRow({ icon, label, value, onPress, destructive }: {
  icon: string; label: string; value?: string; onPress?: () => void; destructive?: boolean;
}) {
  return (
    <TouchableOpacity style={styles.row} onPress={onPress} activeOpacity={onPress ? 0.7 : 1} disabled={!onPress}>
      <Text style={styles.rowIcon}>{icon}</Text>
      <Text style={[styles.rowLabel, destructive && styles.rowLabelDestructive]}>{label}</Text>
      {value && <Text style={styles.rowValue}>{value}</Text>}
      {onPress && <Text style={styles.rowChevron}>›</Text>}
    </TouchableOpacity>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.sectionCard}>
        {children}
      </View>
    </View>
  );
}

export default function SettingsScreen() {
  const insets = useSafeAreaInsets();
  const { user, logout } = useAuth();
  const { t, locale, setLocale, locales, labels, flags } = useLanguage();
  const [langModalVisible, setLangModalVisible] = useState(false);

  const handleLogout = () => {
    Alert.alert(t.nav.logout, "Are you sure?", [
      { text: t.common.cancel, style: "cancel" },
      { text: t.nav.logout, style: "destructive", onPress: logout },
    ]);
  };

  const planColors: Record<string, string> = {
    free: colors.textMuted,
    starter: colors.success,
    pro: colors.primary,
    team: colors.purple,
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <Text style={styles.headerTitle}>{t.settings.title}</Text>
      </View>

      {/* Profile card */}
      <View style={styles.profileCard}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{user?.name?.charAt(0).toUpperCase() ?? "?"}</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.userName}>{user?.name}</Text>
          <Text style={styles.userEmail}>{user?.email}</Text>
        </View>
        <View style={[styles.planBadge, { backgroundColor: `${planColors[user?.plan ?? "free"]}18` }]}>
          <Text style={[styles.planText, { color: planColors[user?.plan ?? "free"] }]}>
            {user?.plan?.toUpperCase() ?? "FREE"}
          </Text>
        </View>
      </View>

      <Section title="Account">
        <SettingRow
          icon="💳"
          label={t.settings.credits}
          value={user?.credit_balance?.toLocaleString() ?? "0"}
        />
        <View style={styles.divider} />
        <SettingRow
          icon="⭐"
          label={t.settings.plan}
          value={user?.plan?.toUpperCase() ?? "FREE"}
        />
      </Section>

      <Section title="Preferences">
        <SettingRow
          icon="🌐"
          label={t.settings.language}
          value={`${flags[locale]} ${labels[locale]}`}
          onPress={() => setLangModalVisible(true)}
        />
      </Section>

      <Section title="App">
        <SettingRow
          icon="ℹ️"
          label={t.settings.version}
          value="1.0.0"
        />
      </Section>

      <Section title="">
        <SettingRow
          icon="🚪"
          label={t.settings.logout}
          onPress={handleLogout}
          destructive
        />
      </Section>

      {/* Language Modal */}
      <Modal visible={langModalVisible} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modal}>
          <View style={[styles.modalHeader, { paddingTop: insets.top + spacing.sm }]}>
            <TouchableOpacity onPress={() => setLangModalVisible(false)}>
              <Text style={styles.modalCancel}>{t.common.cancel}</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>{t.settings.language}</Text>
            <View style={{ width: 60 }} />
          </View>
          <View style={styles.modalContent}>
            {locales.map((l) => (
              <TouchableOpacity
                key={l}
                style={[styles.langRow, l === locale && styles.langRowActive]}
                onPress={() => { setLocale(l as Locale); setLangModalVisible(false); }}
              >
                <Text style={styles.langFlag}>{flags[l as Locale]}</Text>
                <Text style={[styles.langLabel, l === locale && styles.langLabelActive]}>
                  {labels[l as Locale]}
                </Text>
                {l === locale && <Text style={styles.checkmark}>✓</Text>}
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.backgroundSecondary },
  content: { paddingBottom: 48 },
  header: {
    backgroundColor: colors.white,
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.xl,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTitle: { ...typography.xl, ...typography.extrabold, color: colors.text },
  profileCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    backgroundColor: colors.white,
    margin: spacing.xl,
    padding: spacing.lg,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  avatar: {
    width: 48, height: 48, borderRadius: 24,
    backgroundColor: colors.primary,
    alignItems: "center", justifyContent: "center",
  },
  avatarText: { color: colors.white, ...typography.lg, ...typography.bold },
  userName: { ...typography.md, ...typography.bold, color: colors.text },
  userEmail: { ...typography.sm, color: colors.textSecondary, marginTop: 2 },
  planBadge: { borderRadius: radius.full, paddingHorizontal: 10, paddingVertical: 4 },
  planText: { fontSize: 11, fontWeight: "700" },
  section: { paddingHorizontal: spacing.xl, marginBottom: spacing.md },
  sectionTitle: { ...typography.xs, color: colors.textMuted, marginBottom: spacing.sm, textTransform: "uppercase", letterSpacing: 0.8 },
  sectionCard: {
    backgroundColor: colors.white, borderRadius: radius.xl,
    borderWidth: 1, borderColor: colors.border,
    overflow: "hidden",
  },
  row: {
    flexDirection: "row", alignItems: "center", gap: spacing.md,
    paddingHorizontal: spacing.lg, paddingVertical: spacing.lg,
  },
  rowIcon: { fontSize: 20, width: 28, textAlign: "center" },
  rowLabel: { ...typography.base, color: colors.text, flex: 1 },
  rowLabelDestructive: { color: colors.error },
  rowValue: { ...typography.sm, color: colors.textSecondary },
  rowChevron: { fontSize: 20, color: colors.textMuted },
  divider: { height: 1, backgroundColor: colors.border, marginLeft: 56 },
  modal: { flex: 1, backgroundColor: colors.white },
  modalHeader: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: spacing.xl, paddingBottom: spacing.lg,
    borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  modalCancel: { ...typography.base, color: colors.primary },
  modalTitle: { ...typography.md, ...typography.bold, color: colors.text },
  modalContent: { padding: spacing.xl, gap: spacing.sm },
  langRow: {
    flexDirection: "row", alignItems: "center", gap: spacing.md,
    padding: spacing.lg, borderRadius: radius.lg,
    borderWidth: 1.5, borderColor: colors.border,
  },
  langRowActive: { borderColor: colors.primary, backgroundColor: colors.primaryLight },
  langFlag: { fontSize: 24 },
  langLabel: { ...typography.md, color: colors.text, flex: 1 },
  langLabelActive: { color: colors.primary, ...typography.bold },
  checkmark: { fontSize: 18, color: colors.primary, ...typography.bold },
});
