"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  History,
  FileText,
  Network,
  Terminal,
  Layers,
  LogOut,
  ShieldCheck,
  Clock,
  GitCompare,
  Globe,
  Bot,
  Coins,
  GitFork,
} from "lucide-react";
import CytoscapeGraph from "@/components/CytoscapeGraph";
import ShockStudio from "@/components/ShockStudio";
import PnLWaterfall from "@/components/PnLWaterfall";
import BacktestComparison from "@/components/BacktestComparison";
import PortfolioImporter from "@/components/PortfolioImporter";
import NarrativePostMortem from "@/components/NarrativePostMortem";
import HedgeOptimizer from "@/components/HedgeOptimizer";
import TimelinePlayer from "@/components/TimelinePlayer";
import ScenarioDiffViewer from "@/components/ScenarioDiffViewer";
import ExecutiveMemoModal from "@/components/ExecutiveMemoModal";
import RegulatorySignoffModal from "@/components/RegulatorySignoffModal";
import GeospatialMap from "@/components/GeospatialMap";
import StressCopilot from "@/components/StressCopilot";
import LiquidityStudio from "@/components/LiquidityStudio";
import SupplyChainMutationStudio from "@/components/SupplyChainMutationStudio";
import LoginScreen from "@/components/LoginScreen";
import { AuthProvider, useAuth } from "@/context/AuthContext";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5051";

function RiskLatticeDashboard() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<
    | "canvas"
    | "geospatial"
    | "copilot"
    | "liquidity"
    | "mutation"
    | "optimizer"
    | "timeline"
    | "diff"
    | "backtest"
    | "importer"
  >("canvas");

  // Enterprise Governance & Reporting Modals
  const [isMemoOpen, setIsMemoOpen] = useState<boolean>(false);
  const [isSignoffOpen, setIsSignoffOpen] = useState<boolean>(false);

  // State
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] });
  const [nodeShocks, setNodeShocks] = useState<Record<string, any>>({});
  const [portfolioPnl, setPortfolioPnl] = useState<any>(null);
  const [riskMetrics, setRiskMetrics] = useState<any>(null);
  const [criticalPaths, setCriticalPaths] = useState<string[][]>([]);
  const [narrative, setNarrative] = useState<any>(null);

  const [isSimulating, setIsSimulating] = useState(false);
  const [streamingHop, setStreamingHop] = useState<{ hop: number; label: string } | null>(null);

  const [backtestData, setBacktestData] = useState<any>(null);
  const [isBacktesting, setIsBacktesting] = useState(false);

  const [backendStatus, setBackendStatus] = useState<string>("Checking...");

  // Load Initial Graph
  const loadGraph = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/graph`);
      if (res.ok) {
        const data = await res.json();
        setGraphData(data.elements);
        setBackendStatus("Online (50 Nodes)");
      } else {
        setBackendStatus("Offline");
      }
    } catch {
      setBackendStatus("Connecting to :8000...");
    }
  };

  useEffect(() => {
    loadGraph();
  }, []);

  // Run Deterministic Stress Simulation
  const handleSimulate = async (scenarioPrompt: string, directImpulses?: Record<string, number>) => {
    setIsSimulating(true);
    try {
      const body: any = { scenario_name: "Contagion Stress Simulation" };
      if (directImpulses && Object.keys(directImpulses).length > 0) {
        body.direct_impulses = directImpulses;
      } else {
        body.scenario_prompt = scenarioPrompt;
      }

      const res = await fetch(`${API_BASE}/api/v1/stress/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const data = await res.json();
        setNodeShocks(data.simulation.node_shocks);
        setPortfolioPnl(data.simulation.portfolio_pnl);
        setRiskMetrics(data.risk_metrics);
        setCriticalPaths(data.simulation.critical_paths);
        setNarrative(data.narrative);
      }
    } catch (e) {
      console.error("Simulation failed", e);
    } finally {
      setIsSimulating(false);
    }
  };

  // Start Server-Sent Events (SSE) Stream
  const handleStartSSEStream = async (scenarioPrompt: string, directImpulses?: Record<string, number>) => {
    setIsSimulating(true);
    setStreamingHop({ hop: 0, label: "Hop 0: Initializing Vector s^(0)..." });

    let url = `${API_BASE}/api/v1/stress/stream`;
    if (directImpulses && Object.keys(directImpulses).length > 0) {
      url += `?impulses_json=${encodeURIComponent(JSON.stringify(directImpulses))}`;
    } else if (scenarioPrompt) {
      url += `?scenario_prompt=${encodeURIComponent(scenarioPrompt)}`;
    }

    const eventSource = new EventSource(url);

    eventSource.addEventListener("hop_update", (event: any) => {
      try {
        const payload = JSON.parse(event.data);
        setStreamingHop({ hop: payload.hop, label: payload.label });

        // Update active shocks for this hop
        setNodeShocks((prev) => {
          const updated = { ...prev };
          for (const [nid, val] of Object.entries(payload.active_shocks)) {
            updated[nid] = {
              cumulative_shock: val,
              order1_direct: val,
              order2_tier1: 0,
              order3_4_network: 0,
              distress_multiplier: 1.0,
            };
          }
          return updated;
        });
      } catch (e) {
        console.error("SSE parse error", e);
      }
    });

    eventSource.addEventListener("simulation_complete", (event: any) => {
      try {
        const payload = JSON.parse(event.data);
        setStreamingHop(null);
        eventSource.close();
        setIsSimulating(false);
        // After SSE completes, run full math for waterfall & risk metrics
        handleSimulate(scenarioPrompt, directImpulses);
      } catch (e) {
        eventSource.close();
        setIsSimulating(false);
      }
    });

    eventSource.onerror = () => {
      eventSource.close();
      setIsSimulating(false);
      setStreamingHop(null);
    };
  };

  // Run Full Backtest Suite
  const handleRunBacktest = async () => {
    setIsBacktesting(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/backtest/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_id: "all" }),
      });
      if (res.ok) {
        const data = await res.json();
        setBacktestData(data);
      }
    } catch (e) {
      console.error("Backtest failed", e);
    } finally {
      setIsBacktesting(false);
    }
  };

  // Ingest Portfolio
  const handleIngestPortfolio = async (holdings: Record<string, number>) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/portfolio/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Custom Portfolio", holdings }),
      });
      if (res.ok) {
        const data = await res.json();
        alert(`Portfolio Ingested: ${data.sanitized_count} assets normalized.`);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Extract SEC Filing
  const handleExtractFiling = async (chunkText: string, ticker: string) => {
    const res = await fetch(`${API_BASE}/api/v1/graph/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chunk_text: chunkText, company_ticker: ticker }),
    });
    return res.json();
  };

  // Top drawdowns for display
  const topDrawdowns = Object.values(nodeShocks)
    .filter((n: any) => n.node_type === "ASSET" && n.cumulative_shock < 0)
    .sort((a: any, b: any) => a.cumulative_shock - b.cumulative_shock);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#070b12] flex items-center justify-center">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-slate-400 font-mono">Authenticating institutional session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  return (
    <div className="min-h-screen bg-[#070b12] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Header */}
      <header className="px-6 py-3.5 bg-[#0b101b] border-b border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-3 sticky top-0 z-50 backdrop-blur-md">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 text-slate-950 shadow-lg shadow-cyan-500/20">
            <Network className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-black tracking-tight text-white">
                Risk<span className="text-cyan-400">Lattice</span>
              </h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
                v1.0 NEURO-SYMBOLIC
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Cross-Asset Macro Contagion Stress-Tester • 4-Hop Damped Propagation &amp; Copula CVaR
            </p>
          </div>
        </div>

        {/* Navigation Tabs, Quick Actions, Status & User Profile */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex flex-wrap items-center gap-1 bg-slate-900/90 rounded-xl p-1 border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab("canvas")}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg transition font-medium ${
                activeTab === "canvas"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Canvas</span>
            </button>
            <button
              onClick={() => setActiveTab("geospatial")}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg transition font-medium ${
                activeTab === "geospatial"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Globe className="w-3.5 h-3.5" />
              <span>Geospatial</span>
            </button>
            <button
              onClick={() => setActiveTab("copilot")}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg transition font-medium ${
                activeTab === "copilot"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Bot className="w-3.5 h-3.5" />
              <span>AI Copilot</span>
            </button>
            <button
              onClick={() => setActiveTab("liquidity")}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg transition font-medium ${
                activeTab === "liquidity"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Coins className="w-3.5 h-3.5" />
              <span>Liquidity</span>
            </button>
            <button
              onClick={() => setActiveTab("mutation")}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg transition font-medium ${
                activeTab === "mutation"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <GitFork className="w-3.5 h-3.5" />
              <span>Mutation ROI</span>
            </button>
            <button
              onClick={() => setActiveTab("optimizer")}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg transition font-medium ${
                activeTab === "optimizer"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Hedge Optimizer</span>
            </button>
            <button
              onClick={() => setActiveTab("timeline")}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg transition font-medium ${
                activeTab === "timeline"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              <span>Timeline</span>
            </button>
            <button
              onClick={() => setActiveTab("diff")}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg transition font-medium ${
                activeTab === "diff"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <GitCompare className="w-3.5 h-3.5" />
              <span>A/B Diff</span>
            </button>
            <button
              onClick={() => {
                setActiveTab("backtest");
                if (!backtestData) handleRunBacktest();
              }}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg transition font-medium ${
                activeTab === "backtest"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>Backtest</span>
            </button>
            <button
              onClick={() => setActiveTab("importer")}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg transition font-medium ${
                activeTab === "importer"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>10-K &amp; PMS</span>
            </button>
          </div>

          {/* Institutional Fast Action Modals */}
          <div className="flex items-center space-x-1.5">
            <button
              onClick={() => setIsMemoOpen(true)}
              title="Generate Board-Ready Executive Stress Memo"
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/60 text-slate-300 hover:text-white transition text-xs font-semibold"
            >
              <FileText className="w-3.5 h-3.5 text-cyan-400" />
              <span className="hidden xl:inline">Board Memo</span>
            </button>
            <button
              onClick={() => setIsSignoffOpen(true)}
              title="Four-Eyes Governance &amp; Regulatory Audit Sign-off"
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-emerald-500/60 text-slate-300 hover:text-white transition text-xs font-semibold"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden xl:inline">Audit Vault</span>
            </button>
          </div>

          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-300 text-[11px]">{backendStatus}</span>
          </div>

          {/* User Profile & Sign Out */}
          {user && (
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
              <div className="flex items-center space-x-2">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-600 text-white flex items-center justify-center font-bold text-[11px] shadow">
                  {user.name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
                </div>
                <div className="hidden xl:block text-left">
                  <div className="text-[11px] font-bold text-slate-200 leading-tight">
                    {user.name}
                  </div>
                  <div className="text-[9px] text-cyan-400 font-mono">
                    {user.role.replace(/_/g, " ")}
                  </div>
                </div>
              </div>
              <button
                onClick={logout}
                title="Sign out of session"
                className="p-1.5 rounded-lg bg-slate-900 hover:bg-rose-950/60 hover:text-rose-400 border border-slate-800 text-slate-400 transition"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Content Body */}
      <main className="flex-1 p-5 md:p-6 max-w-7xl mx-auto w-full space-y-5">
        {activeTab === "canvas" && (
          <>
            {/* Cytoscape Canvas */}
            <CytoscapeGraph
              elements={graphData}
              nodeShocks={nodeShocks}
              activeHop={streamingHop?.hop ?? null}
            />

            {/* Shock Studio Controls */}
            <ShockStudio
              onSimulate={handleSimulate}
              onStartSSEStream={handleStartSSEStream}
              isSimulating={isSimulating}
              streamingHop={streamingHop}
            />

            {/* Multi-Hop PnL Waterfall & Copula CVaR */}
            <PnLWaterfall
              portfolioPnl={portfolioPnl}
              riskMetrics={riskMetrics}
              criticalPaths={criticalPaths}
              topDrawdowns={topDrawdowns}
            />

            {/* Post-Mortem Narrative Report */}
            <NarrativePostMortem narrative={narrative} />
          </>
        )}

        {activeTab === "geospatial" && <GeospatialMap />}

        {activeTab === "copilot" && <StressCopilot />}

        {activeTab === "liquidity" && <LiquidityStudio />}

        {activeTab === "mutation" && <SupplyChainMutationStudio />}

        {activeTab === "optimizer" && (
          <HedgeOptimizer
            unhedgedPnl={portfolioPnl?.total_pnl ?? -23450000}
            nodeShocks={
              nodeShocks && Object.keys(nodeShocks).length > 0
                ? Object.fromEntries(
                    Object.entries(nodeShocks).map(([k, v]: [string, any]) => [
                      k,
                      typeof v === "object" ? v.cumulative_shock : v,
                    ])
                  )
                : { TSM: -0.4, NVDA: -0.32, AAPL: -0.26, F: -0.22 }
            }
            portfolioNotional={100000000}
          />
        )}

        {activeTab === "timeline" && (
          <TimelinePlayer
            initialShocks={
              nodeShocks && Object.keys(nodeShocks).length > 0
                ? Object.fromEntries(
                    Object.entries(nodeShocks).map(([k, v]: [string, any]) => [
                      k,
                      typeof v === "object" ? v.cumulative_shock : v,
                    ])
                  )
                : { TSM: -0.4 }
            }
            portfolioNotional={100000000}
          />
        )}

        {activeTab === "diff" && <ScenarioDiffViewer />}

        {activeTab === "backtest" && (
          <BacktestComparison
            onRunBacktest={handleRunBacktest}
            isLoading={isBacktesting}
            backtestData={backtestData}
          />
        )}

        {activeTab === "importer" && (
          <PortfolioImporter
            onIngestPortfolio={handleIngestPortfolio}
            onExtractFiling={handleExtractFiling}
          />
        )}
      </main>

      {/* Executive Board-Ready Memorandum Modal */}
      <ExecutiveMemoModal
        isOpen={isMemoOpen}
        onClose={() => setIsMemoOpen(false)}
        scenarioName="Taiwan Strait Blockade & Semiconductor Shock"
        portfolioNotional={100000000}
        pnlLoss={portfolioPnl?.total_pnl ?? -23450000}
        cvar99={riskMetrics?.cvar_99 ?? 29312500}
      />

      {/* Four-Eyes Governance Sign-off & Audit Vault Modal */}
      <RegulatorySignoffModal
        isOpen={isSignoffOpen}
        onClose={() => setIsSignoffOpen(false)}
        runId="run-citadel-202611-001"
        scenarioName="Taiwan Foundry Disruption - High Severity"
        pnlImpact={portfolioPnl?.total_pnl ?? -23450000}
        cvar99={riskMetrics?.cvar_99 ?? 29312500}
      />

      {/* Terminal Footer */}
      <footer className="px-6 py-3 bg-[#0b101b] border-t border-slate-800/80 text-[11px] font-mono text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <Terminal className="w-3.5 h-3.5 text-cyan-500" />
          <span>RiskLattice • Deterministic Python Math Engine + LiteLLM Semantic Router</span>
        </div>
        <div className="flex items-center space-x-4">
          <span>DuckDB 2.0 OLAP</span>
          <span>SciPy CSR Matrix W</span>
          <span>10k Student-t Paths</span>
        </div>
      </footer>
    </div>
  );
}

export default function Home() {
  return (
    <AuthProvider>
      <RiskLatticeDashboard />
    </AuthProvider>
  );
}
