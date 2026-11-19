import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from "react-native";
import { colors } from "../theme/colors";
import { api } from "../config/api";
import { ThreatSnapshot } from "../types";
import { SviGauge } from "../components/SviGauge";
import { ChokePointCard } from "../components/ChokePointCard";
import { ThreatWireCard } from "../components/ThreatWireCard";

interface RadarScreenProps {
  onInjectThreatSuccess?: (res: any) => void;
}

export const RadarScreen: React.FC<RadarScreenProps> = ({ onInjectThreatSuccess }) => {
  const [snapshot, setSnapshot] = useState<ThreatSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isTicking, setIsTicking] = useState(false);
  const [injectingId, setInjectingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchThreats = async () => {
    try {
      setError(null);
      const data = await api.getThreatStatus();
      setSnapshot(data);
    } catch (err: any) {
      setError(err.message || "Failed to connect to backend on :5051");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchThreats();
    // Auto-polling every 8 seconds
    const interval = setInterval(fetchThreats, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleAdvanceTick = async () => {
    setIsTicking(true);
    try {
      const updated = await api.advanceThreatTick();
      setSnapshot(updated);
    } catch (err: any) {
      Alert.alert("Tick Error", err.message);
    } finally {
      setIsTicking(false);
    }
  };

  const handleInjectThreat = async (eventId: string) => {
    setInjectingId(eventId);
    try {
      const result = await api.injectThreat(eventId);
      Alert.alert(
        "⚡ Shock Injected",
        `Simulated ${result.scenario_title}.\nPortfolio Drawdown: ${(result.simulation.portfolio_pnl.drawdown_pct * 100).toFixed(1)}%`
      );
      if (onInjectThreatSuccess) {
        onInjectThreatSuccess(result);
      }
    } catch (err: any) {
      Alert.alert("Injection Failed", err.message);
    } finally {
      setInjectingId(null);
    }
  };

  if (loading && !snapshot) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Connecting to Satellite AIS Feed...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            fetchThreats();
          }}
          tintColor={colors.primary}
        />
      }
    >
      {error ? (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>⚠️ {error}</Text>
          <Text style={styles.errorSub}>Check Settings tab to update API host address.</Text>
        </View>
      ) : null}

      {snapshot ? (
        <>
          <SviGauge
            score={snapshot.svi_index}
            status={snapshot.svi_status}
            threatCount={snapshot.active_threats_count}
            onAdvanceTick={handleAdvanceTick}
            isTicking={isTicking}
          />

          {/* 5 Global Maritime Choke Points */}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>GLOBAL MARITIME CHOKE POINTS</Text>
            <Text style={styles.sectionSub}>Live AIS Speed & Queue Congestion (5 Corridors)</Text>
          </View>

          <View style={styles.cardsContainer}>
            {snapshot.choke_points.map((cp) => (
              <ChokePointCard key={cp.choke_point_id} data={cp} />
            ))}
          </View>

          {/* Threat Wire Feed */}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>GEOPOLITICAL THREAT WIRE</Text>
            <Text style={styles.sectionSub}>Breaking Alerts & 1-Tap Cascade Testing</Text>
          </View>

          <View style={styles.cardsContainer}>
            {snapshot.recent_threats.map((threat) => (
              <ThreatWireCard
                key={threat.event_id}
                threat={threat}
                onInject={handleInjectThreat}
                isInjecting={injectingId === threat.event_id}
              />
            ))}
          </View>
        </>
      ) : null}
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
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: colors.background,
    padding: 24,
  },
  loadingText: {
    color: colors.textSecondary,
    fontSize: 13,
    marginTop: 12,
  },
  errorBanner: {
    backgroundColor: colors.dangerBg,
    borderColor: colors.dangerDark,
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    marginHorizontal: 16,
    marginTop: 12,
  },
  errorText: {
    color: colors.danger,
    fontSize: 12,
    fontWeight: "700",
  },
  errorSub: {
    color: colors.textSecondary,
    fontSize: 11,
    marginTop: 2,
  },
  sectionHeader: {
    paddingHorizontal: 16,
    marginTop: 20,
    marginBottom: 8,
  },
  sectionTitle: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
  sectionSub: {
    color: colors.textSecondary,
    fontSize: 12,
    marginTop: 2,
  },
  cardsContainer: {
    paddingHorizontal: 16,
  },
});
