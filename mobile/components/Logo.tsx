import React from "react";
import { View, Text, StyleSheet } from "react-native";
import Svg, { Rect, Path } from "react-native-svg";
import { colors } from "@/lib/theme";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
}

export function Logo({ size = "md", showText = true }: LogoProps) {
  const iconSize = { sm: 28, md: 36, lg: 52 }[size];
  const textSize = { sm: 15, md: 19, lg: 27 }[size];

  return (
    <View style={styles.container}>
      <LogoMark size={iconSize} />
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
  const r = (size * 12) / 40;
  return (
    <Svg width={size} height={size} viewBox="0 0 40 40">
      <Rect width="40" height="40" rx={r} fill={colors.primary} />
      <Path
        d="M10 30 L10 10 L14 10 L26 24 L26 10 L30 10 L30 30 L26 30 L14 16 L14 30 Z"
        fill="white"
      />
    </Svg>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  text: {
    fontWeight: "800",
    letterSpacing: -0.5,
  },
  nippon: {
    color: colors.primary,
  },
  claw: {
    color: colors.text,
  },
});
