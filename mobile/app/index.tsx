import { View, Text, StyleSheet } from "react-native";
import { useLanguage } from "@/context/LanguageContext";

export default function Index() {
  const { t } = useLanguage();
  return (
    <View style={styles.container}>
      <Text style={styles.text}>{t.nav.login}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center" },
  text: { fontSize: 24, color: "#E63946" },
});
