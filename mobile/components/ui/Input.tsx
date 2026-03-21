import React, { forwardRef } from "react";
import {
  TextInput,
  Text,
  View,
  StyleSheet,
  type TextInputProps,
} from "react-native";
import { colors, radius, typography } from "@/lib/theme";

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
}

export const Input = forwardRef<TextInput, InputProps>(
  ({ label, error, style, ...props }, ref) => {
    return (
      <View style={styles.wrapper}>
        {label && <Text style={styles.label}>{label}</Text>}
        <TextInput
          ref={ref}
          style={[styles.input, error && styles.inputError, style]}
          placeholderTextColor={colors.textMuted}
          autoCapitalize="none"
          autoCorrect={false}
          {...props}
        />
        {error && <Text style={styles.error}>{error}</Text>}
      </View>
    );
  }
);

Input.displayName = "Input";

const styles = StyleSheet.create({
  wrapper: { gap: 6 },
  label: {
    ...typography.sm,
    ...typography.bold,
    color: colors.text,
  },
  input: {
    height: 48,
    borderWidth: 1.5,
    borderColor: colors.borderInput,
    borderRadius: radius.lg,
    paddingHorizontal: 16,
    backgroundColor: colors.white,
    color: colors.text,
    ...typography.base,
  },
  inputError: {
    borderColor: colors.error,
  },
  error: {
    ...typography.xs,
    color: colors.error,
  },
});
