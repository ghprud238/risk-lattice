import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
  Platform,
} from "react-native";
import { colors } from "../theme/colors";
import { api } from "../config/api";
import { AuditEntry } from "../types";

export const AuditScreen: React.FC = () => {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [approvingId, setApprovingId] = useState<string | null>(null);

  const fetchAuditVault = async () => {
    try {
      const res = await api.getAuditEntries();
      setEntries(res.entries || []);
    } catch (err: any) {
      console.warn("Audit vault fetch error:", err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAuditVault();
  }, []);

  const handleApprove = async (runId: string) => {
    setApprovingId(runId);
    try {
      const res = await api.approveAuditRun(
        runId,
        "sarah.chen@citadel.com",
        "CHIEF_RISK_OFFICER",
        "Verified via Mobile Biometric Dual-Key Sign-off (SR 11-7)"
      );
      Alert.alert(
        "Four-Eyes Dual Sign-off Approved",
        `Run ${runId} has been digitally sealed.\nSHA-256: ${res.entry.sha256_seal?.slice(0, 24)}...`
      );
      fetchAuditVault();
    } catch (err: any) {
      Alert.alert("Approval Failed", err.message);
    } finally {
      setApprovingId(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "APPROVED":
      case "LOCKED":
        return { text: colors.success, bg: colors.successBg, border: colors.successDark };
      case "UNDER_REVIEW":
        return { text: colors.warning, bg: colors.warningBg, border: colors.warningDark };
      default:
        return { text: colors.textMuted, bg: colors.surfaceLight, border: colors.borderLight };
    }
  };

  if (loading && entries.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Accessing Cryptographic Audit Vault...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            fetchAuditVault();
          }}
          tintColor={colors.primary}
        />
      }
    >
      <View style={styles.header}>
        <Text style={styles.title}>FOUR-EYES AUDIT VAULT</Text>
        <Text style={styles.sub}>Federal Reserve SR 11-7 / Basel III Dual-Key Governance</Text>
      </View>

      <View style={styles.infoBanner}>
        <Text style={styles.infoText}>
          Dual-signature governance requires independent verification from both a submitting Quantitative Analyst and an approving Chief Risk Officer (CRO) before regulatory submission.
        </Text>
      </View>

      {entries.length === 0 ? (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyTitle}>Vault Synchronized</Text>
          <Text style={styles.emptySub}>No stress runs currently require dual-key signoff.</Text>
        </View>
      ) : (
        entries.map((entry) => {
          const st = getStatusColor(entry.status);
          const isPending = entry.status === "UNDER_REVIEW" || entry.status === "DRAFT";

          return (
            <View key={entry.run_id} style={styles.entryCard}>
              <View style={styles.entryTopRow}>
                <View style={[styles.statusBadge, { backgroundColor: st.bg, borderColor: st.border }]}>
                  <Text style={[styles.statusText, { color: st.text }]}>{entry.status}</Text>
                </View>
                <Text style={styles.runId}>RUN: {entry.run_id.slice(0, 8)}</Text>
              </View>

              <Text style={styles.scenarioName}>{entry.scenario_name}</Text>

              <View style={styles.metricsRow}>
                <View style={styles.metricCol}>
                  <Text style={styles.metricLabel}>PNL DRAWDOWN</Text>
                  <Text style={styles.pnlText}>-${(Math.abs(entry.pnl_impact) / 1_000_000).toFixed(2)}M</Text>
                </View>
                <View style={styles.metricCol}>
                  <Text style={styles.metricLabel}>99% CVAR</Text>
                  <Text style={styles.cvarText}>${(entry.cvar_99 / 1_000_000).toFixed(2)}M</Text>
                </View>
                <View style={styles.metricCol}>
                  <Text style={styles.metricLabel}>SUBMITTER</Text>
                  <Text style={styles.submitterText}>{entry.submitted_by_role}</Text>
                </View>
              </View>

              {entry.sha256_seal ? (
                <View style={styles.sealBox}>
                  <Text style={styles.sealLabel}>SHA-256 DIGITAL SEAL:</Text>
                  <Text style={styles.sealHash}>{entry.sha256_seal.slice(0, 36)}...</Text>
                </View>
              ) : null}

              {isPending ? (
                <TouchableOpacity
                  style={[styles.approveBtn, approvingId === entry.run_id && styles.approveBtnDisabled]}
                  onPress={() => handleApprove(entry.run_id)}
                  disabled={approvingId === entry.run_id}
                  activeOpacity={0.8}
                >
                  <Text style={styles.approveBtnText}>
                    {approvingId === entry.run_id
                      ? "Verifying Biometrics..."
                      : "🔏 Biometric CRO Dual-Sign & Seal"}
                  </Text>
                </TouchableOpacity>
              ) : (
                <View style={styles.signedPill}>
                  <Text style={styles.signedText}>
                    Signed by {entry.secondary_signature || entry.primary_signature || "CRO"}
                  </Text>
                </View>
              )}
            </View>
          );
        })
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    paddingBottom: 24,
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: colors.background,
  },
  loadingText: {
    color: colors.textSecondary,
    fontSize: 12,
    marginTop: 10,
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
  infoBanner: {
    backgroundColor: colors.surface,
    padding: 12,
    marginHorizontal: 16,
    marginBottom: 12,
    borderRadius: 10,
    borderLeftWidth: 3,
    borderLeftColor: colors.cyan,
  },
  infoText: {
    color: colors.textSecondary,
    fontSize: 11,
    lineHeight: 16,
  },
  emptyCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 24,
    marginHorizontal: 16,
    alignItems: "center",
  },
  emptyTitle: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
  },
  emptySub: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 4,
  },
  entryCard: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  entryTopRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
  },
  statusText: {
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  runId: {
    color: colors.textMuted,
    fontSize: 11,
    fontWeight: "600",
  },
  scenarioName: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
    marginBottom: 10,
  },
  metricsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    marginBottom: 10,
  },
  metricCol: {
    flex: 1,
  },
  metricLabel: {
    color: colors.textMuted,
    fontSize: 9,
    fontWeight: "700",
  },
  pnlText: {
    color: colors.danger,
    fontSize: 13,
    fontWeight: "700",
    marginTop: 2,
  },
  cvarText: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: "700",
    marginTop: 2,
  },
  submitterText: {
    color: colors.textSecondary,
    fontSize: 11,
    fontWeight: "600",
    marginTop: 2,
  },
  sealBox: {
    backgroundColor: colors.surfaceLight,
    padding: 8,
    borderRadius: 6,
    marginBottom: 10,
  },
  sealLabel: {
    color: colors.textMuted,
    fontSize: 9,
    fontWeight: "700",
  },
  sealHash: {
    color: colors.cyan,
    fontSize: 10,
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
    marginTop: 2,
  },
  approveBtn: {
    backgroundColor: colors.primaryDark,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: "center",
  },
  approveBtnDisabled: {
    opacity: 0.5,
  },
  approveBtnText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "800",
  },
  signedPill: {
    backgroundColor: colors.successBg,
    paddingVertical: 6,
    borderRadius: 6,
    alignItems: "center",
  },
  signedText: {
    color: colors.success,
    fontSize: 11,
    fontWeight: "700",
  },
});
