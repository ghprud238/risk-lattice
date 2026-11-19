import React, { useState, useEffect } from "react";
import { StyleSheet, View } from "react-native";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";

import { colors } from "./src/theme/colors";
import { api } from "./src/config/api";
import { Header } from "./src/components/Header";
import { TabBar, TabKey } from "./src/components/TabBar";

import { RadarScreen } from "./src/screens/RadarScreen";
import { StressScreen } from "./src/screens/StressScreen";
import { CopilotScreen } from "./src/screens/CopilotScreen";
import { AuditScreen } from "./src/screens/AuditScreen";
import { SettingsScreen } from "./src/screens/SettingsScreen";

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("radar");
  const [isOnline, setIsOnline] = useState<boolean>(false);
  const [currentPersona, setCurrentPersona] = useState<string>("cro");
  const [pendingAuditsCount, setPendingAuditsCount] = useState<number>(1);

  const checkConnection = async () => {
    try {
      await api.checkHealth();
      setIsOnline(true);
    } catch {
      setIsOnline(false);
    }
  };

  const checkAuditEntries = async () => {
    try {
      const res = await api.getAuditEntries();
      const pending = res.entries.filter(
        (e) => e.status === "UNDER_REVIEW" || e.status === "DRAFT"
      );
      setPendingAuditsCount(pending.length);
    } catch {
      // Offline fallback
    }
  };

  useEffect(() => {
    checkConnection();
    checkAuditEntries();
    const interval = setInterval(() => {
      checkConnection();
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  const getPersonaName = () => {
    switch (currentPersona) {
      case "pm":
        return "David Sterling";
      case "analyst":
        return "Alex Kumar";
      case "auditor":
        return "Elena Rostova";
      default:
        return "Sarah Chen, Ph.D.";
    }
  };

  const getPersonaRole = () => {
    switch (currentPersona) {
      case "pm":
        return "PM";
      case "analyst":
        return "Analyst";
      case "auditor":
        return "Auditor";
      default:
        return "CRO";
    }
  };

  const getScreenTitle = () => {
    switch (activeTab) {
      case "radar":
        return "Threat Radar";
      case "stress":
        return "Stress Test";
      case "copilot":
        return "AI Copilot";
      case "audit":
        return "Audit Vault";
      case "settings":
        return "Settings";
    }
  };

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.safeArea} edges={["top", "bottom"]}>
        <StatusBar style="light" />

        <Header
          title={getScreenTitle()}
          isOnline={isOnline}
          userRole={getPersonaRole()}
          userName={getPersonaName()}
          onRefresh={checkConnection}
        />

        <View style={styles.content}>
          {activeTab === "radar" && (
            <RadarScreen
              onInjectThreatSuccess={() => {
                // Switch to stress screen to show simulated waterfall
                setActiveTab("stress");
              }}
            />
          )}
          {activeTab === "stress" && <StressScreen />}
          {activeTab === "copilot" && <CopilotScreen />}
          {activeTab === "audit" && <AuditScreen />}
          {activeTab === "settings" && (
            <SettingsScreen
              currentPersona={currentPersona}
              onPersonaChange={(p) => setCurrentPersona(p)}
            />
          )}
        </View>

        <TabBar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          badgeCount={pendingAuditsCount}
        />
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    flex: 1,
    backgroundColor: colors.background,
  },
});
