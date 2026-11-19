import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from "react-native";
import { colors } from "../theme/colors";
import { api } from "../config/api";
import { SimulateResponse } from "../types";
import { WaterfallCard } from "../components/WaterfallCard";

export const StressScreen: React.FC = () => {
  const [waferShock, setWaferShock] = useState<number>(-0.70);
  const [freightShock, setFreightShock] = useState<number>(1.80);
  const [oilShock, setOilShock] = useState<number>(0.45);
  const [sofrSpread, setSofrSpread] = useState<number>(0.035);

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SimulateResponse | null>(null);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await api.runSimulation({
        scenario_name: "Mobile Cross-Asset Macro Contagion",
        direct_impulses: {
          FOUNDRY_TW: waferShock,
          BALTIC_DRY: freightShock,
          BRENT_CRUDE: oilShock,
          SOFR_SPREAD: sofrSpread,
        },
      });
      setResult(res);
    } catch (err: any) {
      Alert.alert("Simulation Failed", err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.header}>
        <Text style={styles.title}>MACRO STRESS SIMULATOR</Text>
        <Text style={styles.sub}>Adjust systemic factors & revalue 100M portfolio</Text>
      </View>

      {/* Factor Selectors */}
      <View style={styles.factorBox}>
        {/* Taiwan Wafer Export */}
        <View style={styles.factorRow}>
          <View style={styles.factorMeta}>
            <Text style={styles.factorName}>Taiwan Wafer Export</Text>
            <Text style={styles.factorCode}>FOUNDRY_TW</Text>
          </View>
          <View style={styles.buttonGroup}>
            {[-0.30, -0.50, -0.70, -0.90].map((val) => (
              <TouchableOpacity
                key={val}
                style={[styles.valBtn, waferShock === val && styles.valBtnActive]}
                onPress={() => setWaferShock(val)}
              >
                <Text style={[styles.valBtnText, waferShock === val && styles.valBtnTextActive]}>
                  {(val * 100).toFixed(0)}%
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Baltic Dry Shipping */}
        <View style={styles.factorRow}>
          <View style={styles.factorMeta}>
            <Text style={styles.factorName}>Marine Freight Surge</Text>
            <Text style={styles.factorCode}>BALTIC_DRY</Text>
          </View>
          <View style={styles.buttonGroup}>
            {[0.50, 1.00, 1.80].map((val) => (
              <TouchableOpacity
                key={val}
                style={[styles.valBtn, freightShock === val && styles.valBtnActive]}
                onPress={() => setFreightShock(val)}
              >
                <Text style={[styles.valBtnText, freightShock === val && styles.valBtnTextActive]}>
                  +{(val * 100).toFixed(0)}%
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Crude Oil */}
        <View style={styles.factorRow}>
          <View style={styles.factorMeta}>
            <Text style={styles.factorName}>Crude Oil Price</Text>
            <Text style={styles.factorCode}>BRENT_CRUDE</Text>
          </View>
          <View style={styles.buttonGroup}>
            {[0.20, 0.45, 0.80].map((val) => (
              <TouchableOpacity
                key={val}
                style={[styles.valBtn, oilShock === val && styles.valBtnActive]}
                onPress={() => setOilShock(val)}
              >
                <Text style={[styles.valBtnText, oilShock === val && styles.valBtnTextActive]}>
                  +{(val * 100).toFixed(0)}%
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* SOFR Spread */}
        <View style={styles.factorRow}>
          <View style={styles.factorMeta}>
            <Text style={styles.factorName}>SOFR Liquidity Spread</Text>
            <Text style={styles.factorCode}>SOFR_SPREAD</Text>
          </View>
          <View style={styles.buttonGroup}>
            {[0.015, 0.035, 0.050].map((val) => (
              <TouchableOpacity
                key={val}
                style={[styles.valBtn, sofrSpread === val && styles.valBtnActive]}
                onPress={() => setSofrSpread(val)}
              >
                <Text style={[styles.valBtnText, sofrSpread === val && styles.valBtnTextActive]}>
                  +{(val * 10000).toFixed(0)}bps
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Run Button */}
        <TouchableOpacity
          style={[styles.runButton, loading && styles.runButtonDisabled]}
          onPress={handleSimulate}
          disabled={loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.runButtonText}>⚡ Run 4-Hop Contagion & 10k Copula</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Waterfall Output */}
      {result ? (
        <>
          <WaterfallCard
            pnl={result.simulation.portfolio_pnl}
            riskMetrics={result.risk_metrics}
          />

          {/* Marginal Contribution to Risk (MCR) */}
          <View style={styles.mcrCard}>
            <Text style={styles.mcrTitle}>MARGINAL CONTRIBUTION TO RISK (MCR)</Text>
            <Text style={styles.mcrSub}>Decomposed 99% Expected Shortfall by Holding</Text>

            <View style={styles.mcrTable}>
              {Object.entries(result.risk_metrics.marginal_risk).map(([ticker, pct]) => (
                <View key={ticker} style={styles.mcrRow}>
                  <Text style={styles.mcrTicker}>{ticker}</Text>
                  <View style={styles.mcrTrack}>
                    <View
                      style={[
                        styles.mcrFill,
                        {
                          width: `${Math.min(100, Math.max(0, pct * 100))}%`,
                          backgroundColor: pct > 0.3 ? colors.danger : colors.primary,
                        },
                      ]}
                    />
                  </View>
                  <Text style={styles.mcrPct}>{(pct * 100).toFixed(1)}%</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Narrative Summary */}
          {result.narrative ? (
            <View style={styles.narrativeCard}>
              <Text style={styles.narrativeTitle}>GROUNDED NARRATIVE BRIEFING</Text>
              <Text style={styles.narrativeText}>{result.narrative.bottleneck_summary}</Text>
              <View style={styles.hedgeBox}>
                <Text style={styles.hedgeLabel}>RECOMMENDED TAIL HEDGE:</Text>
                <Text style={styles.hedgeText}>{result.narrative.hedge_recommendation}</Text>
              </View>
            </View>
          ) : null}
        </>
      ) : (
        <View style={styles.placeholderCard}>
          <Text style={styles.placeholderText}>
            Tap &ldquo;Run 4-Hop Contagion&rdquo; to evaluate how these macro shocks cascade through Tier-1 suppliers to automotive OEMs.
          </Text>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  contentContainer: {
    paddingBottom: 24,
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 12,
    marginBottom: 8,
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
  factorBox: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.borderLight,
    gap: 14,
  },
  factorRow: {
    gap: 6,
  },
  factorMeta: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  factorName: {
    color: colors.text,
    fontSize: 12,
    fontWeight: "600",
  },
  factorCode: {
    color: colors.cyan,
    fontSize: 10,
    fontWeight: "700",
  },
  buttonGroup: {
    flexDirection: "row",
    gap: 8,
  },
  valBtn: {
    flex: 1,
    backgroundColor: colors.surfaceLight,
    paddingVertical: 7,
    borderRadius: 8,
    alignItems: "center",
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  valBtnActive: {
    backgroundColor: colors.primaryDark,
    borderColor: colors.primary,
  },
  valBtnText: {
    color: colors.textSecondary,
    fontSize: 11,
    fontWeight: "700",
  },
  valBtnTextActive: {
    color: "#fff",
  },
  runButton: {
    backgroundColor: colors.primaryDark,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: "center",
    marginTop: 4,
  },
  runButtonDisabled: {
    opacity: 0.6,
  },
  runButtonText: {
    color: "#fff",
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 0.3,
  },
  placeholderCard: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: 20,
    marginHorizontal: 16,
    borderWidth: 1,
    borderColor: colors.borderLight,
    alignItems: "center",
  },
  placeholderText: {
    color: colors.textMuted,
    fontSize: 12,
    textAlign: "center",
    lineHeight: 18,
  },
  mcrCard: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  mcrTitle: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
  mcrSub: {
    color: colors.textSecondary,
    fontSize: 11,
    marginTop: 1,
    marginBottom: 12,
  },
  mcrTable: {
    gap: 8,
  },
  mcrRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  mcrTicker: {
    color: colors.text,
    fontSize: 12,
    fontWeight: "700",
    width: 44,
  },
  mcrTrack: {
    flex: 1,
    height: 8,
    backgroundColor: colors.backgroundSecondary,
    borderRadius: 4,
    overflow: "hidden",
  },
  mcrFill: {
    height: "100%",
    borderRadius: 4,
  },
  mcrPct: {
    color: colors.textSecondary,
    fontSize: 12,
    fontWeight: "700",
    width: 42,
    textAlign: "right",
  },
  narrativeCard: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: 16,
    marginHorizontal: 16,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  narrativeTitle: {
    color: colors.cyan,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  narrativeText: {
    color: colors.textSecondary,
    fontSize: 12,
    lineHeight: 18,
  },
  hedgeBox: {
    backgroundColor: colors.surfaceLight,
    borderRadius: 8,
    padding: 10,
    marginTop: 10,
    borderLeftWidth: 3,
    borderLeftColor: colors.primary,
  },
  hedgeLabel: {
    color: colors.primary,
    fontSize: 10,
    fontWeight: "700",
    marginBottom: 2,
  },
  hedgeText: {
    color: colors.text,
    fontSize: 11,
    fontWeight: "500",
  },
});
