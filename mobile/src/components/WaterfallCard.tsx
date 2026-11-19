import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { colors } from "../theme/colors";
import { PortfolioPnL, RiskMetricsResult } from "../types";

interface WaterfallCardProps {
  pnl: PortfolioPnL | null;
  riskMetrics: RiskMetricsResult | null;
  notional?: number;
}

export const WaterfallCard: React.FC<WaterfallCardProps> = ({
  pnl,
  riskMetrics,
  notional = 100_000_000,
}) => {
  if (!pnl) {
    return (
      <View style={styles.card}>
        <Text style={styles.emptyText}>No simulation executed. Select a scenario or inject a threat.</Text>
      </View>
    );
  }

  const formatMillions = (val: number) => {
    const abs = Math.abs(val);
    if (abs >= 1_000_000) {
      return `${val < 0 ? "-" : "+"}$${(abs / 1_000_000).toFixed(1)}M`;
    }
    return `${val < 0 ? "-" : "+"}$${(abs / 1_000).toFixed(0)}k`;
  };

  const totalAbs = Math.abs(pnl.hop1_pnl) + Math.abs(pnl.hop2_pnl) + Math.abs(pnl.hop3_4_pnl) || 1;
  const pct1 = (Math.abs(pnl.hop1_pnl) / totalAbs) * 100;
  const pct2 = (Math.abs(pnl.hop2_pnl) / totalAbs) * 100;
  const pct3 = (Math.abs(pnl.hop3_4_pnl) / totalAbs) * 100;

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View>
          <Text style={styles.title}>EXECUTIVE PNL WATERFALL</Text>
          <Text style={styles.subtitle}>Convex 4-Hop Cascade Attribution</Text>
        </View>
        <View style={styles.drawdownBadge}>
          <Text style={styles.drawdownText}>
            {(pnl.drawdown_pct * 100).toFixed(1)}% Drawdown
          </Text>
        </View>
      </View>

      <View style={styles.headlineRow}>
        <Text style={styles.headlineLoss}>{formatMillions(pnl.total_pnl)}</Text>
        <Text style={styles.notionalContext}>on ${ (notional / 1_000_000).toFixed(0) }M Portfolio</Text>
      </View>

      {/* Visual Waterfall Distribution Bar */}
      <View style={styles.barContainer}>
        <View style={[styles.barSegment, { width: `${pct1}%`, backgroundColor: "#f87171" }]} />
        <View style={[styles.barSegment, { width: `${pct2}%`, backgroundColor: "#ef4444" }]} />
        <View style={[styles.barSegment, { width: `${pct3}%`, backgroundColor: "#991b1b" }]} />
      </View>

      {/* 3 Buckets */}
      <View style={styles.bucketsContainer}>
        <View style={styles.bucketRow}>
          <View style={styles.bucketLeft}>
            <View style={[styles.bucketDot, { backgroundColor: "#f87171" }]} />
            <Text style={styles.bucketName}>1st-Order (Direct Hit)</Text>
          </View>
          <Text style={styles.bucketValue}>{formatMillions(pnl.hop1_pnl)}</Text>
        </View>

        <View style={styles.bucketRow}>
          <View style={styles.bucketLeft}>
            <View style={[styles.bucketDot, { backgroundColor: "#ef4444" }]} />
            <Text style={styles.bucketName}>2nd-Order (Tier-1 Suppliers)</Text>
          </View>
          <Text style={styles.bucketValue}>{formatMillions(pnl.hop2_pnl)}</Text>
        </View>

        <View style={styles.bucketRow}>
          <View style={styles.bucketLeft}>
            <View style={[styles.bucketDot, { backgroundColor: "#991b1b" }]} />
            <Text style={styles.bucketName}>3rd/4th-Order (Contagion & Debt)</Text>
          </View>
          <Text style={styles.bucketValue}>{formatMillions(pnl.hop3_4_pnl)}</Text>
        </View>
      </View>

      {/* Copula Tail Risk Footnote */}
      {riskMetrics ? (
        <View style={styles.riskFooter}>
          <View style={styles.riskItem}>
            <Text style={styles.riskLabel}>99% COPULA CVAR</Text>
            <Text style={styles.riskVal}>{(riskMetrics.cvar_99 * 100).toFixed(1)}%</Text>
          </View>
          <View style={styles.riskItem}>
            <Text style={styles.riskLabel}>95% VAR</Text>
            <Text style={styles.riskVal}>{(riskMetrics.var_95 * 100).toFixed(1)}%</Text>
          </View>
          <View style={styles.riskItem}>
            <Text style={styles.riskLabel}>TAIL RATIO</Text>
            <Text style={[styles.riskVal, { color: colors.warning }]}>
              {riskMetrics.tail_ratio.toFixed(1)}x
            </Text>
          </View>
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  emptyText: {
    color: colors.textMuted,
    fontSize: 12,
    textAlign: "center",
    paddingVertical: 12,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  title: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: 12,
    marginTop: 2,
  },
  drawdownBadge: {
    backgroundColor: colors.dangerBg,
    borderColor: colors.dangerDark,
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  drawdownText: {
    color: colors.danger,
    fontSize: 11,
    fontWeight: "800",
  },
  headlineRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 8,
    marginVertical: 12,
  },
  headlineLoss: {
    color: colors.danger,
    fontSize: 32,
    fontWeight: "800",
    letterSpacing: -0.5,
  },
  notionalContext: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: "600",
  },
  barContainer: {
    flexDirection: "row",
    height: 8,
    borderRadius: 4,
    overflow: "hidden",
    marginBottom: 12,
  },
  barSegment: {
    height: "100%",
  },
  bucketsContainer: {
    gap: 8,
  },
  bucketRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 2,
  },
  bucketLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  bucketDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  bucketName: {
    color: colors.textSecondary,
    fontSize: 12,
    fontWeight: "500",
  },
  bucketValue: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "700",
  },
  riskFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  riskItem: {
    alignItems: "center",
  },
  riskLabel: {
    color: colors.textMuted,
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  riskVal: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "700",
    marginTop: 2,
  },
});
