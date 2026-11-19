import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { colors } from "../theme/colors";
import { SviStatus } from "../types";

interface SviGaugeProps {
  score: number;
  status: SviStatus;
  threatCount: number;
  onAdvanceTick?: () => void;
  isTicking?: boolean;
}

export const SviGauge: React.FC<SviGaugeProps> = ({
  score,
  status,
  threatCount,
  onAdvanceTick,
  isTicking = false,
}) => {
  const getStatusColor = () => {
    if (score >= 65 || status === "CRITICAL" || status === "SEVERE") {
      return { text: colors.danger, bg: colors.dangerBg, border: colors.dangerDark };
    }
    if (score >= 35 || status === "ELEVATED") {
      return { text: colors.warning, bg: colors.warningBg, border: colors.warningDark };
    }
    return { text: colors.success, bg: colors.successBg, border: colors.successDark };
  };

  const statusTheme = getStatusColor();

  return (
    <View style={styles.card}>
      <View style={styles.topRow}>
        <View>
          <Text style={styles.label}>SYSTEMIC VULNERABILITY INDEX (SVI)</Text>
          <Text style={styles.subtext}>Global Satellite AIS Maritime Radar</Text>
        </View>

        <View style={[styles.badge, { backgroundColor: statusTheme.bg, borderColor: statusTheme.border }]}>
          <Text style={[styles.badgeText, { color: statusTheme.text }]}>{status}</Text>
        </View>
      </View>

      <View style={styles.scoreRow}>
        <View style={styles.scoreContainer}>
          <Text style={[styles.scoreValue, { color: statusTheme.text }]}>
            {score.toFixed(1)}
          </Text>
          <Text style={styles.scoreMax}>/ 100</Text>
        </View>

        <View style={styles.metaCol}>
          <Text style={styles.metaLabel}>ACTIVE THREAT WIRES</Text>
          <Text style={styles.metaValue}>{threatCount} Priority Events</Text>
          
          <TouchableOpacity
            style={[styles.tickButton, isTicking && styles.tickButtonDisabled]}
            onPress={onAdvanceTick}
            disabled={isTicking}
            activeOpacity={0.7}
          >
            <Text style={styles.tickButtonText}>
              {isTicking ? "Drifting..." : "Advance AIS Drift Tick"}
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Visual meter bar */}
      <View style={styles.meterTrack}>
        <View
          style={[
            styles.meterFill,
            {
              width: `${Math.min(100, Math.max(0, score))}%`,
              backgroundColor: statusTheme.text,
            },
          ]}
        />
      </View>
      <View style={styles.meterLabels}>
        <Text style={styles.meterSub}>0 (Resilient)</Text>
        <Text style={styles.meterSub}>50 (Watch)</Text>
        <Text style={styles.meterSub}>100 (Systemic Ruin)</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: 16,
    marginHorizontal: 16,
    marginTop: 12,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  topRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  label: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
  subtext: {
    color: colors.textSecondary,
    fontSize: 12,
    marginTop: 2,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  scoreRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginVertical: 14,
  },
  scoreContainer: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 4,
  },
  scoreValue: {
    fontSize: 44,
    fontWeight: "800",
    letterSpacing: -1,
  },
  scoreMax: {
    color: colors.textMuted,
    fontSize: 16,
    fontWeight: "600",
  },
  metaCol: {
    alignItems: "flex-end",
    gap: 3,
  },
  metaLabel: {
    color: colors.textMuted,
    fontSize: 10,
    fontWeight: "600",
    letterSpacing: 0.5,
  },
  metaValue: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
  },
  tickButton: {
    marginTop: 6,
    backgroundColor: colors.surfaceLight,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  tickButtonDisabled: {
    opacity: 0.5,
  },
  tickButtonText: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: "600",
  },
  meterTrack: {
    height: 6,
    backgroundColor: colors.backgroundSecondary,
    borderRadius: 3,
    overflow: "hidden",
    marginTop: 4,
  },
  meterFill: {
    height: "100%",
    borderRadius: 3,
  },
  meterLabels: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 4,
  },
  meterSub: {
    color: colors.textMuted,
    fontSize: 9,
    fontWeight: "500",
  },
});
