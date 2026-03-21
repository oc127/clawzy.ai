import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { colors } from "@/lib/theme";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
}

export function Logo({ size = "md", showText = true }: LogoProps) {
  const iconSize = { sm: 28, md: 36, lg: 52 }[size];
  const textSize = { sm: 15, md: 19, lg: 27 }[size];
  const fontSize = { sm: 13, md: 17, lg: 24 }[size];
  const borderRadius = { sm: 7, md: 9, lg: 13 }[size];

  return (
    <View style={styles.container}>
      <View style={[styles.mark, { width: iconSize, height: iconSize, borderRadius }]}>
        <Text style={[styles.markText, { fontSize }]}>N</Text>
      </View>
      {showText && (
        <Text style={[styles.text, { fontSize: textSize }]}>
          <Text style={styles.nippon}>Nippon</Text>
          <Text style={styles.claw}>Claw</Text>
        </Text>
      )}
    </View>
  );
}

export function LogoMark({ size = 36 }: { size?: number }) {
  const borderRadius = Math.round(size * 0.28);
  const fontSize = Math.round(size * 0.48);
  return (
    <View style={[styles.mark, { width: size, height: size, borderRadius }]}>
      <Text style={[styles.markText, { fontSize }]}>N</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  mark: {
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },
  markText: {
    color: "#FFFFFF",
    fontWeight: "900",
    letterSpacing: -0.5,
  },
  text: {
    fontWeight: "800",
    letterSpacing: -0.5,
  },
  nippon: {
    color: colors.primary,
  },
  claw: {
    color: "#222222",
  },
});
