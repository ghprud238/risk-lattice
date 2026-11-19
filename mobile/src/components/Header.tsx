import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { colors } from "../theme/colors";

interface HeaderProps {
  title: string;
  subtitle?: string;
  isOnline: boolean;
  userRole?: string;
  userName?: string;
  onRefresh?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  isOnline,
  userRole = "CRO",
  userName = "Sarah Chen",
  onRefresh,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.leftCol}>
        <View style={styles.brandRow}>
          <View style={styles.logoPill}>
            <Text style={styles.logoText}>RL</Text>
          </View>
          <Text style={styles.title}>{title}</Text>
        </View>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      </View>

      <View style={styles.rightCol}>
        <TouchableOpacity style={styles.statusPill} onPress={onRefresh} activeOpacity={0.7}>
          <View
            style={[
              styles.statusDot,
              { backgroundColor: isOnline ? colors.success : colors.danger },
            ]}
          />
          <Text style={styles.statusText}>{isOnline ? "LIVE :5051" : "OFFLINE"}</Text>
        </TouchableOpacity>
        <Text style={styles.userBadge}>{userRole} · {userName.split(" ")[0]}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 12,
    backgroundColor: colors.background,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  leftCol: {
    flex: 1,
  },
  brandRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  logoPill: {
    backgroundColor: colors.primaryDark,
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  logoText: {
    color: "#fff",
    fontWeight: "800",
    fontSize: 12,
    letterSpacing: 0.5,
  },
  title: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "700",
    letterSpacing: -0.3,
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: 12,
    marginTop: 2,
  },
  rightCol: {
    alignItems: "flex-end",
    gap: 4,
  },
  statusPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: colors.surface,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    color: colors.textSecondary,
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  userBadge: {
    color: colors.textMuted,
    fontSize: 11,
    fontWeight: "600",
  },
});
