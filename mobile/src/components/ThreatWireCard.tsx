import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { colors } from "../theme/colors";
import { ThreatEvent } from "../types";

interface ThreatWireCardProps {
  threat: ThreatEvent;
  onInject: (eventId: string) => void;
  isInjecting?: boolean;
}

export const ThreatWireCard: React.FC<ThreatWireCardProps> = ({
  threat,
  onInject,
  isInjecting = false,
}) => {
  const getSeverityStyle = () => {
    switch (threat.severity) {
      case "CRITICAL":
        return { text: colors.danger, bg: colors.dangerBg, border: colors.dangerDark };
      case "HIGH":
        return { text: colors.warning, bg: colors.warningBg, border: colors.warningDark };
      default:
        return { text: colors.primary, bg: colors.cyanBg, border: colors.primaryDark };
    }
  };

  const sev = getSeverityStyle();

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View style={[styles.sevBadge, { backgroundColor: sev.bg, borderColor: sev.border }]}>
          <Text style={[styles.sevText, { color: sev.text }]}>{threat.severity}</Text>
        </View>
        <Text style={styles.source}>{threat.source}</Text>
        <Text style={styles.time}>{threat.timestamp.split("T")[1]?.slice(0, 5) || "Live"}</Text>
      </View>

      <Text style={styles.headline}>{threat.headline}</Text>

      {threat.details ? (
        <Text style={styles.details} numberOfLines={2}>
          {threat.details}
        </Text>
      ) : null}

      <View style={styles.footerRow}>
        <View style={styles.nodesContainer}>
          <Text style={styles.nodesLabel}>IMPACT:</Text>
          <View style={styles.nodePills}>
            {threat.affected_nodes.map((node) => (
              <View key={node} style={styles.nodePill}>
                <Text style={styles.nodeText}>{node}</Text>
              </View>
            ))}
            <Text style={styles.impactPct}>
              {(threat.raw_supply_impact_pct * 100).toFixed(0)}%
            </Text>
          </View>
        </View>

        <TouchableOpacity
          style={[styles.injectButton, isInjecting && styles.injectButtonDisabled]}
          onPress={() => onInject(threat.event_id)}
          disabled={isInjecting}
          activeOpacity={0.7}
        >
          <Text style={styles.injectButtonText}>
            {isInjecting ? "Simulating..." : "⚡ Inject Shock"}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 8,
  },
  sevBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 1,
  },
  sevText: {
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  source: {
    color: colors.textSecondary,
    fontSize: 11,
    fontWeight: "600",
    flex: 1,
  },
  time: {
    color: colors.textMuted,
    fontSize: 10,
  },
  headline: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "700",
    lineHeight: 18,
    marginBottom: 6,
  },
  details: {
    color: colors.textSecondary,
    fontSize: 11,
    lineHeight: 15,
    marginBottom: 10,
  },
  footerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  nodesContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    flex: 1,
  },
  nodesLabel: {
    color: colors.textMuted,
    fontSize: 9,
    fontWeight: "700",
  },
  nodePills: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    flexWrap: "wrap",
  },
  nodePill: {
    backgroundColor: colors.surfaceLight,
    paddingHorizontal: 5,
    paddingVertical: 2,
    borderRadius: 4,
  },
  nodeText: {
    color: colors.cyan,
    fontSize: 10,
    fontWeight: "700",
  },
  impactPct: {
    color: colors.danger,
    fontSize: 10,
    fontWeight: "700",
    marginLeft: 2,
  },
  injectButton: {
    backgroundColor: colors.primaryDark,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
  },
  injectButtonDisabled: {
    opacity: 0.5,
  },
  injectButtonText: {
    color: "#fff",
    fontSize: 11,
    fontWeight: "700",
  },
});
