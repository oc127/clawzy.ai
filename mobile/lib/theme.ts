export const colors = {
  primary: "#FF385C",
  primaryDark: "#E31C5F",
  primaryLight: "#FFF0F2",
  background: "#FFFFFF",
  backgroundSecondary: "#F7F7F7",
  border: "#EBEBEB",
  borderInput: "#B0B0B0",
  text: "#222222",
  textSecondary: "#717171",
  textMuted: "#B0B0B0",
  success: "#10B981",
  warning: "#F59E0B",
  error: "#EF4444",
  white: "#FFFFFF",
  purple: "#8B5CF6",
  indigoLight: "#EEF2FF",
  errorLight: "#FEF2F2",
  errorBorder: "#FECACA",
  dangerLight: "#FEE2E2",
  shadow: "rgba(0,0,0,0.08)",
  // Gradient stops (used as flat fallback too)
  gradientBlue: ["#3B82F6", "#8B5CF6"] as [string, string],
  gradientGreen: ["#10B981", "#34D399"] as [string, string],
  gradientOrange: ["#F59E0B", "#FBBF24"] as [string, string],
  gradientPurple: ["#8B5CF6", "#EC4899"] as [string, string],
  gradientTeal: ["#06B6D4", "#3B82F6"] as [string, string],
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  full: 999,
};

export const typography = {
  xs: { fontSize: 11, lineHeight: 16 },
  sm: { fontSize: 13, lineHeight: 18 },
  base: { fontSize: 15, lineHeight: 22 },
  md: { fontSize: 17, lineHeight: 24 },
  lg: { fontSize: 20, lineHeight: 28 },
  xl: { fontSize: 24, lineHeight: 32 },
  xxl: { fontSize: 30, lineHeight: 38 },
  bold: { fontWeight: "700" as const },
  semibold: { fontWeight: "600" as const },
  extrabold: { fontWeight: "800" as const },
};

export const shadow = {
  sm: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  md: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 4,
  },
  lg: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 8,
  },
};
