import React, { useEffect, useState, useRef, useCallback } from "react";
import {
  View, Text, ScrollView, TextInput, TouchableOpacity,
  KeyboardAvoidingView, Platform, StyleSheet, ActivityIndicator,
} from "react-native";
import { useLocalSearchParams, router } from "expo-router";
import { useLanguage } from "@/context/LanguageContext";
import {
  getAgent, getConversations, getMessages, createConversation,
  getApiHost,
  type Agent, type Message, type Conversation,
} from "@/lib/api";
import { getAccessToken } from "@/lib/storage";
import { colors, spacing, radius, typography } from "@/lib/theme";

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <View style={[styles.bubbleRow, isUser && styles.bubbleRowUser]}>
      {!isUser && (
        <View style={styles.agentAvatar}>
          <Text style={{ fontSize: 14 }}>🤖</Text>
        </View>
      )}
      <View style={[styles.bubble, isUser ? styles.bubbleUser : styles.bubbleAssistant]}>
        <Text style={[styles.bubbleText, isUser && styles.bubbleTextUser]}>
          {msg.content}
        </Text>
      </View>
    </View>
  );
}

export default function AgentChatScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { t } = useLanguage();
  const scrollRef = useRef<ScrollView>(null);

  const [agent, setAgent] = useState<Agent | null>(null);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [streamingText, setStreamingText] = useState("");

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const [a, convs] = await Promise.all([getAgent(id), getConversations(id)]);
      setAgent(a);
      if (convs.length > 0) {
        setConversation(convs[0]);
        const msgs = await getMessages(id, convs[0].id);
        setMessages(msgs);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }, [messages, streamingText]);

  const sendMessage = async () => {
    if (!input.trim() || sending || !id) return;
    const userText = input.trim();
    setInput("");
    setSending(true);
    setStreamingText("");

    // Create conversation if needed
    let convId = conversation?.id;
    if (!convId) {
      try {
        const conv = await createConversation(id);
        setConversation(conv);
        convId = conv.id;
      } catch {
        setSending(false);
        return;
      }
    }

    // Add user message locally
    const userMsg: Message = {
      id: `local-${Date.now()}`,
      role: "user",
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    // Stream response
    try {
      const token = await getAccessToken();
      const res = await fetch(
        `${getApiHost()}/api/v1/agents/${id}/conversations/${convId}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ content: userText }),
        }
      );

      if (!res.ok) throw new Error("Failed");

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No reader");

      const decoder = new TextDecoder();
      let fullText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split("\n").filter((l) => l.startsWith("data: "));
        for (const line of lines) {
          const data = line.slice(6);
          if (data === "[DONE]") continue;
          try {
            const parsed = JSON.parse(data);
            const delta = parsed.choices?.[0]?.delta?.content ?? "";
            fullText += delta;
            setStreamingText(fullText);
          } catch {
            // ignore parse errors
          }
        }
      }

      setMessages((prev) => [
        ...prev,
        {
          id: `local-${Date.now() + 1}`,
          role: "assistant",
          content: fullText,
          created_at: new Date().toISOString(),
        },
      ]);
      setStreamingText("");
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `local-err-${Date.now()}`,
          role: "assistant",
          content: t.common.error,
          created_at: new Date().toISOString(),
        },
      ]);
      setStreamingText("");
    } finally {
      setSending(false);
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
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={0}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => {
            if (router.canGoBack()) router.back();
            else router.replace("/(tabs)/agents");
          }}
          style={styles.backBtn}
          hitSlop={{ top: 12, bottom: 12, left: 8, right: 8 }}
          accessibilityRole="button"
          accessibilityLabel={t.common.back}
        >
          <Text style={styles.backChevron}>←</Text>
          <Text style={styles.backLabel}>{t.common.back}</Text>
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={styles.agentName} numberOfLines={1}>{agent?.name}</Text>
          <Text style={styles.agentModel} numberOfLines={1}>{agent?.model_name}</Text>
        </View>
        <View style={[styles.statusDot, { backgroundColor: agent?.status === "running" ? colors.success : colors.textMuted }]} />
      </View>

      {/* Messages */}
      <ScrollView
        ref={scrollRef}
        style={styles.messages}
        contentContainerStyle={styles.messagesContent}
        showsVerticalScrollIndicator={false}
      >
        {messages.length === 0 && !streamingText ? (
          <View style={styles.emptyChat}>
            <Text style={{ fontSize: 40 }}>🤖</Text>
            <Text style={styles.emptyChatTitle}>{agent?.name}</Text>
            <Text style={styles.emptyChatSubtitle}>{t.chat.noMessages}</Text>
          </View>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            {streamingText ? (
              <MessageBubble
                msg={{ id: "streaming", role: "assistant", content: streamingText, created_at: "" }}
              />
            ) : null}
            {sending && !streamingText ? (
              <View style={styles.typingIndicator}>
                <View style={styles.agentAvatar}>
                  <Text style={{ fontSize: 14 }}>🤖</Text>
                </View>
                <View style={styles.typingBubble}>
                  <ActivityIndicator size="small" color={colors.textMuted} />
                  <Text style={styles.typingText}>{t.chat.typing}</Text>
                </View>
              </View>
            ) : null}
          </>
        )}
      </ScrollView>

      {/* Input */}
      <View style={styles.inputBar}>
        <TextInput
          style={styles.textInput}
          placeholder={t.chat.placeholder}
          placeholderTextColor={colors.textMuted}
          value={input}
          onChangeText={setInput}
          multiline
          maxLength={4000}
          returnKeyType="default"
        />
        <TouchableOpacity
          style={[styles.sendBtn, (!input.trim() || sending) && styles.sendBtnDisabled]}
          onPress={sendMessage}
          disabled={!input.trim() || sending}
          activeOpacity={0.8}
        >
          <Text style={styles.sendIcon}>↑</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.backgroundSecondary },
  loadingContainer: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: colors.background },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingTop: 56,
    paddingBottom: spacing.md,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingVertical: 4,
    paddingRight: 8,
    maxWidth: "42%",
  },
  backChevron: { fontSize: 20, color: colors.primary, fontWeight: "600" },
  backLabel: { ...typography.sm, color: colors.primary, fontWeight: "600" },
  agentName: { ...typography.md, ...typography.bold, color: colors.text },
  agentModel: { ...typography.xs, color: colors.textMuted },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  messages: { flex: 1 },
  messagesContent: { padding: spacing.lg, gap: spacing.md, flexGrow: 1 },
  emptyChat: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.sm, paddingTop: 80 },
  emptyChatTitle: { ...typography.lg, ...typography.bold, color: colors.text },
  emptyChatSubtitle: { ...typography.base, color: colors.textSecondary },
  bubbleRow: { flexDirection: "row", alignItems: "flex-end", gap: spacing.sm },
  bubbleRowUser: { justifyContent: "flex-end" },
  agentAvatar: {
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: "#EEF2FF",
    alignItems: "center", justifyContent: "center",
    marginBottom: 2,
  },
  bubble: {
    maxWidth: "80%",
    borderRadius: radius.xl,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  bubbleUser: {
    backgroundColor: colors.primary,
    borderBottomRightRadius: 4,
  },
  bubbleAssistant: {
    backgroundColor: colors.white,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: colors.border,
  },
  bubbleText: { ...typography.base, color: colors.text, lineHeight: 22 },
  bubbleTextUser: { color: colors.white },
  typingIndicator: { flexDirection: "row", alignItems: "flex-end", gap: spacing.sm },
  typingBubble: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.white,
    borderRadius: radius.xl,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  typingText: { ...typography.sm, color: colors.textSecondary },
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    paddingBottom: 28,
    backgroundColor: colors.white,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  textInput: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    borderWidth: 1.5,
    borderColor: colors.borderInput,
    borderRadius: radius.xl,
    paddingHorizontal: spacing.lg,
    paddingTop: 11,
    paddingBottom: 11,
    color: colors.text,
    ...typography.base,
    backgroundColor: colors.backgroundSecondary,
  },
  sendBtn: {
    width: 44, height: 44,
    borderRadius: 22,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },
  sendBtnDisabled: { backgroundColor: colors.border },
  sendIcon: { color: colors.white, fontSize: 20, fontWeight: "700", marginTop: -2 },
});
