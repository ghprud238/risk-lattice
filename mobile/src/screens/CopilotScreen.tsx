import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { colors } from "../theme/colors";
import { api } from "../config/api";
import { CopilotResponse } from "../types";

interface MessageItem {
  id: string;
  sender: "user" | "copilot";
  text: string;
  response?: CopilotResponse;
  timestamp: string;
}

export const CopilotScreen: React.FC = () => {
  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: "1",
      sender: "copilot",
      text: "Hello Sarah. I am RiskLattice Copilot, grounded in SEC 10-K disclosures and deterministic contagion math. How can I assist your risk evaluation today?",
      timestamp: "Just now",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const suggestedQueries = [
    "Why is Ford hit if TSMC is the only shock?",
    "What is our indirect exposure to Taiwan?",
    "How do we hedge against a Hormuz energy spike?",
  ];

  const handleSend = async (queryText?: string) => {
    const q = (queryText || input).trim();
    if (!q || loading) return;

    const userMsg: MessageItem = {
      id: Date.now().toString(),
      sender: "user",
      text: q,
      timestamp: "Now",
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const resp = await api.askCopilot(q);
      const botMsg: MessageItem = {
        id: (Date.now() + 1).toString(),
        sender: "copilot",
        text: resp.answer,
        response: resp,
        timestamp: "Now",
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errMsg: MessageItem = {
        id: (Date.now() + 1).toString(),
        sender: "copilot",
        text: `Error connecting to Copilot: ${err.message}. Make sure backend is running on :5051.`,
        timestamp: "Now",
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={Platform.OS === "ios" ? 80 : 0}
    >
      <View style={styles.header}>
        <Text style={styles.title}>AI CHIEF RISK OFFICER COPILOT</Text>
        <Text style={styles.sub}>SEC 10-K Grounded · Zero Hallucination Math</Text>
      </View>

      {/* Suggested chips */}
      <View style={styles.chipRow}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipScroll}>
          {suggestedQueries.map((sq, i) => (
            <TouchableOpacity
              key={i}
              style={styles.chip}
              onPress={() => handleSend(sq)}
              activeOpacity={0.7}
            >
              <Text style={styles.chipText}>{sq}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Messages */}
      <ScrollView style={styles.msgList} contentContainerStyle={styles.msgContent}>
        {messages.map((m) => (
          <View
            key={m.id}
            style={[
              styles.msgBubble,
              m.sender === "user" ? styles.userBubble : styles.botBubble,
            ]}
          >
            {m.sender === "copilot" && m.response ? (
              <View style={styles.intentBadge}>
                <Text style={styles.intentText}>{m.response.intent}</Text>
              </View>
            ) : null}

            <Text style={[styles.msgText, m.sender === "user" && styles.userMsgText]}>
              {m.text}
            </Text>

            {/* Citations from 10-K */}
            {m.response?.citations && m.response.citations.length > 0 ? (
              <View style={styles.citationsBox}>
                <Text style={styles.citationHeading}>SEC 10-K VERBATIM GROUNDING:</Text>
                {m.response.citations.map((c, idx) => (
                  <Text key={idx} style={styles.quoteText}>
                    &ldquo;{c.quote}&rdquo; — <Text style={styles.quoteSource}>{c.source}</Text>
                  </Text>
                ))}
              </View>
            ) : null}

            <Text style={styles.timestamp}>{m.timestamp}</Text>
          </View>
        ))}

        {loading ? (
          <View style={[styles.msgBubble, styles.botBubble, styles.loadingBubble]}>
            <ActivityIndicator size="small" color={colors.primary} />
            <Text style={styles.thinkingText}>Grounding against 10-K disclosures...</Text>
          </View>
        ) : null}
      </ScrollView>

      {/* Input */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder="Ask Copilot about risk exposures..."
          placeholderTextColor={colors.textMuted}
          value={input}
          onChangeText={setInput}
          onSubmitEditing={() => handleSend()}
          returnKeyType="send"
        />
        <TouchableOpacity
          style={[styles.sendBtn, (!input.trim() || loading) && styles.sendBtnDisabled]}
          onPress={() => handleSend()}
          disabled={!input.trim() || loading}
        >
          <Text style={styles.sendBtnText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 6,
  },
  title: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
  sub: {
    color: colors.textSecondary,
    fontSize: 12,
    marginTop: 2,
  },
  chipRow: {
    paddingVertical: 6,
  },
  chipScroll: {
    paddingHorizontal: 16,
    gap: 8,
  },
  chip: {
    backgroundColor: colors.surface,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  chipText: {
    color: colors.textSecondary,
    fontSize: 11,
    fontWeight: "500",
  },
  msgList: {
    flex: 1,
  },
  msgContent: {
    padding: 16,
    gap: 12,
  },
  msgBubble: {
    borderRadius: 12,
    padding: 12,
    maxWidth: "88%",
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: colors.primaryDark,
  },
  botBubble: {
    alignSelf: "flex-start",
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  loadingBubble: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  thinkingText: {
    color: colors.textSecondary,
    fontSize: 12,
  },
  intentBadge: {
    alignSelf: "flex-start",
    backgroundColor: colors.surfaceLight,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginBottom: 6,
  },
  intentText: {
    color: colors.cyan,
    fontSize: 9,
    fontWeight: "700",
  },
  msgText: {
    color: colors.text,
    fontSize: 13,
    lineHeight: 18,
  },
  userMsgText: {
    color: "#fff",
  },
  citationsBox: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  citationHeading: {
    color: colors.textMuted,
    fontSize: 9,
    fontWeight: "700",
    marginBottom: 4,
  },
  quoteText: {
    color: colors.textSecondary,
    fontSize: 11,
    fontStyle: "italic",
    lineHeight: 15,
  },
  quoteSource: {
    color: colors.primary,
    fontStyle: "normal",
    fontWeight: "600",
  },
  timestamp: {
    color: colors.textMuted,
    fontSize: 9,
    alignSelf: "flex-end",
    marginTop: 4,
  },
  inputContainer: {
    flexDirection: "row",
    padding: 12,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    alignItems: "center",
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: colors.background,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    color: colors.text,
    fontSize: 13,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  sendBtn: {
    backgroundColor: colors.primaryDark,
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 8,
  },
  sendBtnDisabled: {
    opacity: 0.4,
  },
  sendBtnText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "700",
  },
});
