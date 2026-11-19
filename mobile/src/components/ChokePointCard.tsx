import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { colors } from "../theme/colors";
import { ChokePointTelemetry } from "../types";

interface ChokePointCardProps {
  data: ChokePointTelemetry;
}

export const ChokePointCard: React.FC<ChokePointCardProps> = ({ data }) => {
  const isSevere = data.congestion_index > 1.8 || data.status === "CRITICAL";
  const isElevated = data.congestion_index > 1.2 || data.status === "ELEVATED";

  const statusColor = isSevere
    ? colors.danger
    : isElevated
    ? colors.warning
    : colors.success;

  const speedDropPct = ((data.baseline_speed_knots - data.median_speed_knots) / data.baseline_speed_knots) * 100;

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.titleCol}>
          <Text style={styles.name}>{data.name}</Text>
          <Text style={styles.weight}>Global Weight: {(data.criticality_weight * 100).toFixed(0)}%</Text>
        </View>
        <View style={[styles.statusBadge, { borderColor: statusColor }]}>
          <Text style={[styles.statusText, { color: statusColor }]}>{data.status}</Text>
        </View>
      </View>

      <View style={styles.grid}>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>ACTIVE QUEUE</Text>
          <Text style={styles.metricValue}>{data.active_vessels} <Text style={styles.metricSub}>ships</Text></Text>
          <Text style={styles.metricDiff}>Base: {data.baseline_vessels}</Text>
        </View>

        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>FLEET SPEED</Text>
          <Text style={[styles.metricValue, { color: speedDropPct > 30 ? colors.danger : colors.text }]}>
            {data.median_speed_knots.toFixed(1)} <Text style={styles.metricSub}>kts</Text>
          </Text>
          <Text style={styles.metricDiff}>
            {speedDropPct > 0 ? `-${speedDropPct.toFixed(0)}% drop` : "Normal"}
          </Text>
        </View>

        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>CONGESTION (C)</Text>
          <Text style={[styles.metricValue, { color: data.congestion_index > 1.5 ? colors.danger : colors.text }]}>
            {data.congestion_index.toFixed(2)}x
          </Text>
          <Text style={styles.metricDiff}>Disrupt: {(data.disruption_prob * 100).toFixed(0)}%</Text>
        </View>

        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>DEMURRAGE</Text>
          <Text style={[styles.metricValue, { color: data.demurrage_surge_pct > 50 ? colors.danger : colors.warning }]}>
            +{data.demurrage_surge_pct.toFixed(0)}%
          </Text>
          <Text style={styles.metricDiff}>Charter surge</Text>
        </View>
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
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  titleCol: {
    flex: 1,
  },
  name: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
  },
  weight: {
    color: colors.textMuted,
    fontSize: 10,
    marginTop: 1,
  },
  statusBadge: {
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
    backgroundColor: colors.surfaceLight,
  },
  statusText: {
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  grid: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  metricItem: {
    flex: 1,
  },
  metricLabel: {
    color: colors.textMuted,
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  metricValue: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
    marginTop: 2,
  },
  metricSub: {
    fontSize: 10,
    fontWeight: "400",
    color: colors.textSecondary,
  },
  metricDiff: {
    color: colors.textMuted,
    fontSize: 9,
    marginTop: 1,
  },
});
