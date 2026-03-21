import { Tabs } from "expo-router";
import { View, StyleSheet } from "react-native";
import { colors, radius } from "@/lib/theme";
import { useLanguage } from "@/context/LanguageContext";

// Inline SVG-based tab icons (no extra lib needed)
function HomeIcon({ focused }: { focused: boolean }) {
  return (
    <View style={[styles.icon, focused && styles.iconActive]}>
      <View style={[styles.iconInner, { backgroundColor: focused ? colors.white : "transparent" }]} />
    </View>
  );
}

function TabBarIcon({ label, focused }: { label: string; focused: boolean }) {
  const icons: Record<string, string> = {
    home: "⊞",
    agents: "🤖",
    discover: "✦",
    settings: "⚙",
  };
  return (
    <View style={[styles.tabIcon, focused && styles.tabIconActive]}>
      <View>
        {/* We rely on Expo's default icon rendering via tabBarIcon */}
      </View>
    </View>
  );
}

export default function TabsLayout() {
  const { t } = useLanguage();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarLabelStyle: styles.tabLabel,
        tabBarIconStyle: { marginTop: 2 },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: t.tabs.home,
          tabBarIcon: ({ focused }) => (
            <TabIcon emoji="⊞" focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="agents"
        options={{
          title: t.tabs.agents,
          tabBarIcon: ({ focused }) => (
            <TabIcon emoji="🤖" focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="discover"
        options={{
          title: t.tabs.discover,
          tabBarIcon: ({ focused }) => (
            <TabIcon emoji="✦" focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: t.tabs.settings,
          tabBarIcon: ({ focused }) => (
            <TabIcon emoji="⚙" focused={focused} />
          ),
        }}
      />
    </Tabs>
  );
}

function TabIcon({ emoji, focused }: { emoji: string; focused: boolean }) {
  return (
    <View style={[styles.tabIconWrapper, focused && styles.tabIconWrapperActive]}>
      <View>
        {/* Text used for emoji-based icon */}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: colors.white,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    height: 84,
    paddingBottom: 20,
    paddingTop: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 8,
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: "600",
    marginTop: 2,
  },
  tabIcon: {},
  tabIconActive: {},
  icon: { width: 22, height: 22, borderRadius: 6 },
  iconActive: { backgroundColor: colors.primary },
  iconInner: { flex: 1, borderRadius: 4 },
  tabIconWrapper: {
    width: 28,
    height: 28,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.sm,
  },
  tabIconWrapperActive: {
    backgroundColor: colors.primaryLight,
  },
});
