import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from "react-native";
import { colors } from "../theme/colors";
import { api, getApiBaseUrl, setApiBaseUrl } from "../config/api";

interface SettingsScreenProps {
  onPersonaChange?: (persona: string) => void;
  currentPersona?: string;
}

export const SettingsScreen: React.FC<SettingsScreenProps> = ({
  onPersonaChange,
  currentPersona = "cro",
}) => {
  const [apiUrl, setApiUrl] = useState(getApiBaseUrl());
  const [testing, setTesting] = useState(false);
  const [healthStatus, setHealthStatus] = useState<string | null>(null);

  const personas = [
    { id: "cro", name: "Sarah Chen, Ph.D.", role: "Chief Risk Officer", org: "Citadel Global Equities" },
    { id: "pm", name: "David Sterling", role: "Senior Portfolio Manager", org: "Citadel TMT Long/Short" },
    { id: "analyst", name: "Alex Kumar", role: "Quantitative Risk Analyst", org: "Risk Engineering" },
    { id: "auditor", name: "Elena Rostova", role: "Model Validation Auditor", org: "SR 11-7 Compliance" },
  ];

  const handleSaveUrl = () => {
    setApiBaseUrl(apiUrl);
    Alert.alert("API Endpoint Updated", `Connecting to ${apiUrl}`);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setHealthStatus(null);
    try {
      const res = await api.checkHealth();
      setHealthStatus(`Online: ${res.total_nodes} nodes, ${res.total_edges} edges in DuckDB.`);
      Alert.alert("Connection Success", `Connected to RiskLattice FastAPI server at ${apiUrl}`);
    } catch (err: any) {
      setHealthStatus(`Offline: ${err.message}`);
      Alert.alert("Connection Failed", `Could not reach ${apiUrl}.\n\nTip: If testing on a physical phone, use your Mac's Wi-Fi LAN IP (e.g. http://192.168.1.X:5051) instead of localhost.`);
    } finally {
      setTesting(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>MOBILE TERMINAL CONFIGURATION</Text>
        <Text style={styles.sub}>Server Gateway Routing & Enterprise Personas</Text>
      </View>

      {/* Backend Connection Box */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>BACKEND SERVER GATEWAY</Text>
        <Text style={styles.cardSub}>FastAPI REST & Server-Sent Events (SSE) Endpoint</Text>

        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={apiUrl}
            onChangeText={setApiUrl}
            placeholder="http://localhost:5051"
            placeholderTextColor={colors.textMuted}
            autoCapitalize="none"
            autoCorrect={false}
          />
          <TouchableOpacity style={styles.saveBtn} onPress={handleSaveUrl}>
            <Text style={styles.saveBtnText}>Save</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={[styles.testBtn, testing && styles.testBtnDisabled]}
          onPress={handleTestConnection}
          disabled={testing}
        >
          {testing ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.testBtnText}>⚡ Ping Server Health</Text>
          )}
        </TouchableOpacity>

        {healthStatus ? (
          <View style={styles.healthBanner}>
            <Text style={styles.healthText}>{healthStatus}</Text>
          </View>
        ) : null}

        <View style={styles.quickUrls}>
          <Text style={styles.quickLabel}>QUICK PRESETS:</Text>
          <View style={styles.quickPills}>
            <TouchableOpacity
              style={styles.quickPill}
              onPress={() => {
                setApiUrl("http://localhost:5051");
                setApiBaseUrl("http://localhost:5051");
              }}
            >
              <Text style={styles.quickPillText}>iOS Simulator (:5051)</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.quickPill}
              onPress={() => {
                setApiUrl("http://10.0.2.2:5051");
                setApiBaseUrl("http://10.0.2.2:5051");
              }}
            >
              <Text style={styles.quickPillText}>Android Emulator (:5051)</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* RBAC Persona Switcher */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>ENTERPRISE RBAC PERSONAS</Text>
        <Text style={styles.cardSub}>Switch simulated Google Workspace identity</Text>

        <View style={styles.personaList}>
          {personas.map((p) => {
            const isSelected = currentPersona === p.id;
            return (
              <TouchableOpacity
                key={p.id}
                style={[styles.personaItem, isSelected && styles.personaItemActive]}
                onPress={() => onPersonaChange && onPersonaChange(p.id)}
                activeOpacity={0.8}
              >
                <View style={styles.personaLeft}>
                  <Text style={[styles.personaName, isSelected && styles.personaNameActive]}>
                    {p.name}
                  </Text>
                  <Text style={styles.personaRole}>{p.role} · {p.org}</Text>
                </View>
                {isSelected ? (
                  <View style={styles.activeCheck}>
                    <Text style={styles.activeCheckText}>ACTIVE</Text>
                  </View>
                ) : null}
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Architecture Invariants */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>SECURITY & ARCHITECTURAL INVARIANTS</Text>
        <Text style={styles.infoLine}>• <Text style={styles.bold}>Rule P-01 Local Privacy:</Text> Portfolio dollar balances never leave backend server.</Text>
        <Text style={styles.infoLine}>• <Text style={styles.bold}>ADR-002 Pure AST Engine:</Text> Math engine contains 0 network imports.</Text>
        <Text style={styles.infoLine}>• <Text style={styles.bold}>Deterministic Bit-Exactness:</Text> Pinned PCG64 random generator (seed=42).</Text>
        <Text style={styles.infoLine}>• <Text style={styles.bold}>SR 11-7 Dual Sign-off:</Text> Secondary CRO approval enforced on mobile.</Text>
      </View>
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
  card: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  cardTitle: {
    color: colors.text,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  cardSub: {
    color: colors.textSecondary,
    fontSize: 11,
    marginTop: 2,
    marginBottom: 12,
  },
  inputRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 10,
  },
  input: {
    flex: 1,
    backgroundColor: colors.background,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    color: colors.text,
    fontSize: 12,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  saveBtn: {
    backgroundColor: colors.surfaceLight,
    paddingHorizontal: 14,
    justifyContent: "center",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  saveBtnText: {
    color: colors.text,
    fontSize: 11,
    fontWeight: "700",
  },
  testBtn: {
    backgroundColor: colors.primaryDark,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: "center",
  },
  testBtnDisabled: {
    opacity: 0.5,
  },
  testBtnText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "700",
  },
  healthBanner: {
    marginTop: 10,
    backgroundColor: colors.surfaceLight,
    padding: 8,
    borderRadius: 6,
  },
  healthText: {
    color: colors.success,
    fontSize: 11,
    fontWeight: "600",
  },
  quickUrls: {
    marginTop: 12,
    gap: 6,
  },
  quickLabel: {
    color: colors.textMuted,
    fontSize: 9,
    fontWeight: "700",
  },
  quickPills: {
    flexDirection: "row",
    gap: 6,
    flexWrap: "wrap",
  },
  quickPill: {
    backgroundColor: colors.background,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  quickPillText: {
    color: colors.cyan,
    fontSize: 10,
    fontWeight: "600",
  },
  personaList: {
    gap: 8,
  },
  personaItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: colors.surfaceLight,
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  personaItemActive: {
    borderColor: colors.primary,
    backgroundColor: "rgba(56, 189, 248, 0.1)",
  },
  personaLeft: {
    flex: 1,
  },
  personaName: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "700",
  },
  personaNameActive: {
    color: colors.primary,
  },
  personaRole: {
    color: colors.textSecondary,
    fontSize: 11,
    marginTop: 2,
  },
  activeCheck: {
    backgroundColor: colors.primaryDark,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  activeCheckText: {
    color: "#fff",
    fontSize: 9,
    fontWeight: "800",
  },
  infoLine: {
    color: colors.textSecondary,
    fontSize: 11,
    lineHeight: 18,
    marginTop: 4,
  },
  bold: {
    color: colors.text,
    fontWeight: "700",
  },
});
