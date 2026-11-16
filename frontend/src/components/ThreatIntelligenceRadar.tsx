"use client";

import React, { useState, useEffect } from "react";
import {
  Radio,
  Anchor,
  AlertTriangle,
  Flame,
  Zap,
  RefreshCw,
  ArrowRight,
  TrendingUp,
  ShieldAlert,
  Send,
  Sliders,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5051";

interface ChokePoint {
  choke_point_id: string;
  name: string;
  lat: number;
  lng: number;
  baseline_daily_vessels: number;
  current_vessel_count: number;
  transit_speed_knots: number;
  baseline_speed_knots: number;
  status: string;
  criticality_weight: number;
  demurrage_spike_pct: number;
  congestion_index: number;
  disruption_probability: number;
}

interface ThreatEvent {
  event_id: string;
  timestamp: string;
  headline: string;
  source: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  choke_point_id: string;
  affected_nodes: string[];
  raw_supply_impact_pct: number;
  details: string;
  injected: boolean;
}

interface ThreatIntelligenceSnapshot {
  timestamp: string;
  systemic_vulnerability_index: number;
  total_active_vessels: number;
  vulnerable_assets: string[];
  choke_points: ChokePoint[];
  active_threats: ThreatEvent[];
}

interface Props {
  onInjectShock?: (scenarioName: string, directImpulses: Record<string, number>) => void;
}

export default function ThreatIntelligenceRadar({ onInjectShock }: Props) {
  const [data, setData] = useState<ThreatIntelligenceSnapshot | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isTickLoading, setIsTickLoading] = useState<boolean>(false);
  const [selectedThreat, setSelectedThreat] = useState<ThreatEvent | null>(null);

  // Custom Threat Composer State
  const [customHeadline, setCustomHeadline] = useState("");
  const [customChokePoint, setCustomChokePoint] = useState("GEO_TAIWAN_STRAIT");
  const [customSeverity, setCustomSeverity] = useState("HIGH");
  const [customImpact, setCustomImpact] = useState(-0.35);
  const [customNodes, setCustomNodes] = useState("TSM, NVDA, AAPL");
  const [isComposing, setIsComposing] = useState(false);

  const fetchStatus = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/threats/ais/status`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
        if (json.active_threats?.length > 0 && !selectedThreat) {
          setSelectedThreat(json.active_threats[0]);
        }
      }
    } catch (e) {
      console.error("Failed to load AIS threat status", e);
    } finally {
      setIsLoading(false);
    }
  };

  const advanceTick = async () => {
    setIsTickLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/threats/ais/tick`, { method: "POST" });
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (e) {
      console.error("Tick failed", e);
    } finally {
      setIsTickLoading(false);
    }
  };

  const handleInjectThreat = async (threat: ThreatEvent) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/threats/inject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_id: threat.event_id }),
      });
      if (res.ok) {
        const injection = await res.json();
        if (onInjectShock) {
          onInjectShock(injection.recommended_scenario_name, injection.direct_impulses);
        } else {
          alert(`Injected impulses for ${threat.headline}: ${JSON.stringify(injection.direct_impulses)}`);
        }
      }
    } catch (e) {
      console.error("Failed to inject threat", e);
    }
  };

  const handleCreateCustomThreat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customHeadline.trim()) return;

    const nodesList = customNodes
      .split(",")
      .map((n) => n.trim().toUpperCase())
      .filter((n) => n.length > 0);

    try {
      const res = await fetch(`${API_BASE}/api/v1/threats/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          headline: customHeadline,
          source: "Manual Intelligence Dispatch / CRO Desk",
          severity: customSeverity,
          choke_point_id: customChokePoint,
          affected_nodes: nodesList,
          raw_supply_impact_pct: customImpact,
          details: "Analyst-entered geopolitical contingency scenario.",
        }),
      });

      if (res.ok) {
        setCustomHeadline("");
        setIsComposing(false);
        fetchStatus();
      }
    } catch (err) {
      console.error("Failed to ingest custom threat", err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const getSviColor = (svi: number) => {
    if (svi >= 70) return "text-rose-400 border-rose-500/60 bg-rose-950/40";
    if (svi >= 45) return "text-amber-400 border-amber-500/60 bg-amber-950/40";
    if (svi >= 25) return "text-yellow-400 border-yellow-500/60 bg-yellow-950/40";
    return "text-emerald-400 border-emerald-500/60 bg-emerald-950/40";
  };

  return (
    <div className="space-y-6">
      {/* Top Banner: SVI Index & Live AIS Status */}
      <div className="bg-[#0b101b] border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center space-x-2.5">
              <span className="p-2 rounded-xl bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 flex items-center justify-center shadow-lg shadow-cyan-500/10">
                <Radio className="w-5 h-5 animate-pulse" />
              </span>
              <div>
                <div className="flex items-center space-x-2">
                  <h2 className="text-xl font-bold text-white tracking-tight">
                    Live Threat Intelligence Feed &amp; Satellite AIS Radar
                  </h2>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping inline-block" />
                    <span>STREAM ONLINE</span>
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5 max-w-2xl">
                  Real-time maritime choke-point telemetry (Taiwan Strait, Malacca, Suez, Hormuz, Panama) tracking commercial fleet speed collapse, queue backlogs, demurrage surges, and breaking news alerts.
                </p>
              </div>
            </div>
          </div>

          {/* SVI Gauge & Fast Actions */}
          <div className="flex flex-wrap items-center gap-4">
            {data && (
              <div
                className={`p-3.5 rounded-2xl border flex items-center space-x-3.5 ${getSviColor(
                  data.systemic_vulnerability_index
                )}`}
              >
                <div className="text-right">
                  <div className="text-[10px] font-mono uppercase tracking-wider font-semibold opacity-80">
                    Systemic Vulnerability Index
                  </div>
                  <div className="text-2xl font-black font-mono leading-none">
                    {data.systemic_vulnerability_index.toFixed(1)}
                    <span className="text-xs font-normal opacity-70"> / 100</span>
                  </div>
                </div>
                <Flame className="w-8 h-8 stroke-[2]" />
              </div>
            )}

            <div className="flex items-center space-x-2">
              <button
                onClick={advanceTick}
                disabled={isTickLoading}
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/60 text-slate-300 hover:text-white transition text-xs font-semibold disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isTickLoading ? "animate-spin" : ""}`} />
                <span>Simulate AIS Tick</span>
              </button>

              <button
                onClick={() => setIsComposing(!isComposing)}
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>Dispatch Threat Alert</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Custom Threat Dispatch Drawer (Collapsible) */}
      {isComposing && (
        <form
          onSubmit={handleCreateCustomThreat}
          className="bg-[#0b101b] border border-cyan-500/40 rounded-2xl p-5 space-y-4 shadow-xl"
        >
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-white">
                Dispatch Breaking Threat Wire Event
              </h3>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">
              Directly translates to shock vector s^(0)
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="md:col-span-2 space-y-1.5">
              <label className="text-slate-300 font-medium">Headline / Breaking Wire</label>
              <input
                type="text"
                required
                placeholder="e.g. Taiwan Strait: Typhoon Gaemi Halts All Container Shipping Out of Kaohsiung"
                value={customHeadline}
                onChange={(e) => setCustomHeadline(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Choke Point</label>
              <select
                value={customChokePoint}
                onChange={(e) => setCustomChokePoint(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-cyan-500"
              >
                <option value="GEO_TAIWAN_STRAIT">Taiwan Strait</option>
                <option value="GEO_MALACCA">Strait of Malacca</option>
                <option value="GEO_SUEZ">Suez Canal / Red Sea</option>
                <option value="GEO_HORMUZ">Strait of Hormuz</option>
                <option value="GEO_PANAMA">Panama Canal</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Severity</label>
              <select
                value={customSeverity}
                onChange={(e) => setCustomSeverity(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-cyan-500"
              >
                <option value="LOW">LOW (Localized friction)</option>
                <option value="MEDIUM">MEDIUM (Transit queue surge)</option>
                <option value="HIGH">HIGH (Severe lane restriction)</option>
                <option value="CRITICAL">CRITICAL (Total naval blockade)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">
                Supply Impact: {(customImpact * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="-0.70"
                max="-0.05"
                step="0.05"
                value={customImpact}
                onChange={(e) => setCustomImpact(parseFloat(e.target.value))}
                className="w-full accent-cyan-400 bg-slate-800 h-2 rounded-lg cursor-pointer"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Affected Nodes (Tickers)</label>
              <input
                type="text"
                value={customNodes}
                onChange={(e) => setCustomNodes(e.target.value)}
                placeholder="TSM, NVDA, AAPL, F"
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={() => setIsComposing(false)}
              className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold shadow-lg shadow-cyan-500/20"
            >
              Publish &amp; Broadcast Alert
            </button>
          </div>
        </form>
      )}

      {/* 5 AIS Maritime Choke Points Telemetry Cards */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Anchor className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Satellite AIS Telemetry &bull; Key Maritime Corridors
            </h3>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            {data?.total_active_vessels || 0} Commercial Vessels Monitored
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {data?.choke_points.map((cp) => {
            const isSevere = cp.status === "BLOCKADE" || cp.status === "MILITARY_EXERCISE";
            return (
              <div
                key={cp.choke_point_id}
                className="bg-[#0b101b] border border-slate-800 rounded-xl p-4 flex flex-col justify-between space-y-3 hover:border-slate-700 transition"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span
                      className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold ${
                        isSevere
                          ? "bg-rose-950/80 text-rose-400 border border-rose-800/60"
                          : cp.status === "ELEVATED_QUEUE"
                          ? "bg-amber-950/80 text-amber-400 border border-amber-800/60"
                          : "bg-emerald-950/80 text-emerald-400 border border-emerald-800/60"
                      }`}
                    >
                      {cp.status.replace(/_/g, " ")}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      {(cp.criticality_weight * 100).toFixed(0)}% WT
                    </span>
                  </div>

                  <h4 className="text-xs font-bold text-white mt-2 leading-tight">
                    {cp.name}
                  </h4>
                </div>

                <div className="space-y-1.5 text-[11px] font-mono">
                  <div className="flex justify-between text-slate-400">
                    <span>Active Queue:</span>
                    <span className="font-bold text-white">
                      {cp.current_vessel_count} / {cp.baseline_daily_vessels}
                    </span>
                  </div>

                  <div className="flex justify-between text-slate-400">
                    <span>Transit Speed:</span>
                    <span className={`font-bold ${cp.transit_speed_knots < 8 ? "text-rose-400" : "text-emerald-400"}`}>
                      {cp.transit_speed_knots} kts
                    </span>
                  </div>

                  <div className="flex justify-between text-slate-400">
                    <span>Congestion:</span>
                    <span className={`font-bold ${cp.congestion_index > 2.0 ? "text-amber-400" : "text-slate-300"}`}>
                      {cp.congestion_index}x
                    </span>
                  </div>

                  <div className="flex justify-between text-slate-400">
                    <span>Demurrage:</span>
                    <span className={`font-bold ${cp.demurrage_spike_pct > 30 ? "text-rose-400" : "text-slate-400"}`}>
                      +{cp.demurrage_spike_pct}%
                    </span>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono">
                  <span className="text-slate-500">Risk Prob:</span>
                  <span className={`font-bold ${cp.disruption_probability > 0.5 ? "text-rose-400" : "text-slate-300"}`}>
                    {(cp.disruption_probability * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Threat Wire Feed & Injection Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Feed List */}
        <div className="lg:col-span-2 bg-[#0b101b] border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Active Geopolitical &amp; Maritime Threat Wires
              </h3>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              Click any wire to inspect &amp; inject
            </span>
          </div>

          <div className="space-y-2.5">
            {data?.active_threats.map((threat) => {
              const isSelected = selectedThreat?.event_id === threat.event_id;
              return (
                <div
                  key={threat.event_id}
                  onClick={() => setSelectedThreat(threat)}
                  className={`p-3.5 rounded-xl border transition cursor-pointer flex flex-col justify-between space-y-2 ${
                    isSelected
                      ? "bg-slate-900 border-cyan-500/80 shadow-lg shadow-cyan-500/10"
                      : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold ${
                            threat.severity === "CRITICAL"
                              ? "bg-rose-950/80 text-rose-400 border border-rose-800/60"
                              : threat.severity === "HIGH"
                              ? "bg-amber-950/80 text-amber-400 border border-amber-800/60"
                              : "bg-cyan-950/80 text-cyan-400 border border-cyan-800/60"
                          }`}
                        >
                          {threat.severity}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          {threat.source}
                        </span>
                      </div>
                      <h4 className="text-xs font-bold text-white">
                        {threat.headline}
                      </h4>
                    </div>

                    <div className="flex items-center space-x-1 shrink-0">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleInjectThreat(threat);
                        }}
                        title="Inject directly into stress simulation"
                        className="px-2.5 py-1.5 rounded-lg bg-cyan-950 text-cyan-400 hover:bg-cyan-500 hover:text-slate-950 border border-cyan-800 text-[10px] font-mono font-bold transition flex items-center space-x-1"
                      >
                        <Zap className="w-3 h-3" />
                        <span>Inject</span>
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between text-[10px] text-slate-400 font-mono pt-1 border-t border-slate-800/60">
                    <div className="flex items-center space-x-1">
                      <span>Affected:</span>
                      {threat.affected_nodes.slice(0, 4).map((node) => (
                        <span key={node} className="px-1.5 py-0.5 rounded bg-slate-900 text-slate-300">
                          {node}
                        </span>
                      ))}
                      {threat.affected_nodes.length > 4 && (
                        <span>+{threat.affected_nodes.length - 4}</span>
                      )}
                    </div>
                    <span>Supply Shock: {(threat.raw_supply_impact_pct * 100).toFixed(0)}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Selected Threat Detail Drawer */}
        <div className="bg-[#0b101b] border border-slate-800 rounded-2xl p-5 flex flex-col justify-between space-y-4">
          {selectedThreat ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-xs font-mono font-bold text-cyan-400">
                  {selectedThreat.event_id}
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  {new Date(selectedThreat.timestamp).toLocaleTimeString()} UTC
                </span>
              </div>

              <div>
                <h3 className="text-sm font-bold text-white leading-snug">
                  {selectedThreat.headline}
                </h3>
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                  {selectedThreat.details}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 text-xs font-mono">
                <div className="text-[10px] uppercase font-bold text-slate-400">
                  Impulse Translation Mapping
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Target Choke Point:</span>
                  <span className="text-white font-bold">{selectedThreat.choke_point_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Gross Supply Impact:</span>
                  <span className="text-rose-400 font-bold">
                    {(selectedThreat.raw_supply_impact_pct * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Severity Tier:</span>
                  <span className="text-amber-400 font-bold">{selectedThreat.severity}</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="text-[10px] uppercase font-bold text-slate-400 font-mono">
                  Downstream Vulnerable Entities
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {selectedThreat.affected_nodes.map((node) => (
                    <span
                      key={node}
                      className="px-2 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-cyan-300 font-bold"
                    >
                      {node}
                    </span>
                  ))}
                </div>
              </div>

              <button
                onClick={() => handleInjectThreat(selectedThreat)}
                className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition flex items-center justify-center space-x-2"
              >
                <Zap className="w-4 h-4" />
                <span>Inject Live Shock into Simulation</span>
              </button>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500 text-xs font-mono">
              Select a threat wire to inspect impulse mapping
            </div>
          )}

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 font-mono">
            Direct impulse vectors ($s^{(0)}$) apply exponential tier decay across downstream recipients before 4-hop propagation.
          </div>
        </div>
      </div>
    </div>
  );
}
