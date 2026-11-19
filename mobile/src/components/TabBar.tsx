import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { colors } from "../theme/colors";

export type TabKey = "radar" | "stress" | "copilot" | "audit" | "settings";

interface TabBarProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  badgeCount?: number;
}

export const TabBar: React.FC<TabBarProps> = ({
  activeTab,
  onTabChange,
  badgeCount = 0,
}) => {
  const tabs: { key: TabKey; label: string; icon: string }[] = [
    { key: "radar", label: "Radar", icon: "📡" },
    { key: "stress", label: "Stress", icon: "📊" },
    { key: "copilot", label: "Copilot", icon: "🤖" },
    { key: "audit", label: "Vault", icon: "🔏" },
    { key: "settings", label: "Config", icon: "⚙️" },
  ];

  return (
    <View style={styles.container}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.key;
        return (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tabItem, isActive && styles.tabItemActive]}
            onPress={() => onTabChange(tab.key)}
            activeOpacity={0.7}
          >
            <View style={styles.iconContainer}>
              <Text style={styles.icon}>{tab.icon}</Text>
              {tab.key === "audit" && badgeCount > 0 ? (
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{badgeCount}</Text>
                </View>
              ) : null}
            </View>
            <Text style={[styles.label, isActive && styles.labelActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingVertical: 8,
    paddingHorizontal: 8,
  },
  tabItem: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 4,
    borderRadius: 8,
  },
  tabItemActive: {
    backgroundColor: "rgba(56, 189, 248, 0.08)",
  },
  iconContainer: {
    position: "relative",
  },
  icon: {
    fontSize: 20,
    marginBottom: 2,
  },
  badge: {
    position: "absolute",
    top: -4,
    right: -8,
    backgroundColor: colors.danger,
    borderRadius: 8,
    paddingHorizontal: 4,
    paddingVertical: 1,
    minWidth: 16,
    alignItems: "center",
  },
  badgeText: {
    color: "#fff",
    fontSize: 9,
    fontWeight: "800",
  },
  label: {
    color: colors.textMuted,
    fontSize: 10,
    fontWeight: "600",
  },
  labelActive: {
    color: colors.primary,
    fontWeight: "700",
  },
});
