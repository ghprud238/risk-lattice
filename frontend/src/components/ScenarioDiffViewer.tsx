"use client";

import React, { useState, useEffect } from "react";
import {
  GitCompare,
  RefreshCw,
} from "lucide-react";

interface NodeDiffRecord {
  node_id: string;
  shock_a: number;
  shock_b: number;
  delta_shock: number;
  pnl_a: number;
  pnl_b: number;
  delta_pnl: number;
  status: "AMPLIFIED" | "DE_RISKED" | "UNCHANGED";
  relative_change_pct: number;
}

interface ScenarioDiffResult {
  scenario_a_name: string;
  scenario_b_name: string;
  pnl_a: number;
  pnl_b: number;
  delta_pnl: number;
  cvar_99_a: number;
  cvar_99_b: number;
  delta_cvar_99: number;
  net_improvement_pct: number;
  amplified_nodes_count: number;
  de_risked_nodes_count: number;
  unchanged_nodes_count: number;
  node_diffs: NodeDiffRecord[];
  top_de_risked_nodes: Array<{ node_id: string; delta_pnl: number; status: string; relative_change_pct: number }>;
  top_amplified_nodes: Array<{ node_id: string; delta_pnl: number; status: string; relative_change_pct: number }>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5051";

const SCENARIO_A = "Taiwan Strait Blockade (Unhedged)";
const SCENARIO_B = "Dual-Sourced Re-routing + SOXX Put Hedge";

export default function ScenarioDiffViewer() {
  const [diffResult, setDiffResult] = useState<ScenarioDiffResult | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const runDiff = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/scenario/diff`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_a_name: SCENARIO_A,
          scenario_b_name: SCENARIO_B,
          shocks_a: { TSM: -0.40, NVDA: -0.35, AAPL: -0.28, F: -0.22, BALTIC_DRY: -0.30 },
          shocks_b: { TSM: -0.15, NVDA: -0.12, AAPL: -0.25, F: -0.32, BALTIC_DRY: -0.10 },
          positions: {
            TSM: 20000000,
            NVDA: 25000000,
            AAPL: 20000000,
            F: 10000000,
            BALTIC_DRY: 5000000,
          },
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setDiffResult(data);
      }
    } catch (e) {
      console.error("Diff failed", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    runDiff();
  }, []);

  const filteredNodes = diffResult?.node_diffs.filter((n) => {
    if (filterStatus === "ALL") return true;
    return n.status === filterStatus;
  }) || [];

  return (
    <div className="bg-[#0b101b] border border-slate-800 rounded-xl p-6 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <GitCompare className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              Side-by-Side Scenario Diffing &amp; A/B Risk Attribution
            </h2>
            <p className="text-xs text-slate-400">
              PRD Section 16 • Delta PnL, CVaR Mitigation &amp; Structural Network Divergence
            </p>
          </div>
        </div>

        <button
          onClick={runDiff}
          disabled={isLoading}
          className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-200 font-bold flex items-center space-x-2 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-cyan-400" : ""}`} />
          <span>Re-compute Diff</span>
        </button>
      </div>

      {/* Scenario Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-900/40 p-4 rounded-xl border border-slate-800 text-xs">
        <div className="space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-400">Scenario A (Baseline)</span>
          <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 text-slate-200 font-semibold font-mono">
            {SCENARIO_A}
          </div>
        </div>
        <div className="space-y-1">
          <span className="text-[10px] font-mono uppercase text-cyan-400">Scenario B (Mitigated / Counterfactual)</span>
          <div className="p-2.5 rounded-lg bg-slate-950/80 border border-cyan-900/40 text-cyan-200 font-semibold font-mono">
            {SCENARIO_B}
          </div>
        </div>
      </div>

      {diffResult && (
        <div className="space-y-6">
          {/* High-level Differential KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
              <div className="text-[11px] text-slate-400">Net PnL Delta (B - A)</div>
              <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                +${diffResult.delta_pnl.toLocaleString()}
              </div>
              <div className="text-[10px] text-emerald-500">Loss reduction achieved in B</div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
              <div className="text-[11px] text-slate-400">Tail CVaR (99%) Delta</div>
              <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                -${Math.abs(diffResult.delta_cvar_99).toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-500">
                {diffResult.net_improvement_pct.toFixed(1)}% tail risk compression
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
              <div className="text-[11px] text-slate-400">De-risked Nodes</div>
              <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                {diffResult.de_risked_nodes_count} Assets
              </div>
              <div className="text-[10px] text-slate-500">Shocks reduced by &gt;15%</div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
              <div className="text-[11px] text-slate-400">Amplified Nodes</div>
              <div className="text-xl font-bold font-mono text-rose-400 mt-1">
                {diffResult.amplified_nodes_count} Assets
              </div>
              <div className="text-[10px] text-rose-500">Secondary bottleneck shifts</div>
            </div>
          </div>

          {/* Filter Bar & Diff Table */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="text-xs font-bold text-slate-200">
                Component Differential Matrix
              </div>
              <div className="flex items-center space-x-1.5 text-xs">
                {["ALL", "DE_RISKED", "AMPLIFIED", "UNCHANGED"].map((st) => (
                  <button
                    key={st}
                    onClick={() => setFilterStatus(st)}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-mono transition ${
                      filterStatus === st
                        ? "bg-cyan-500 text-slate-950 font-bold"
                        : "bg-slate-950 text-slate-400 hover:text-white"
                    }`}
                  >
                    {st.replace(/_/g, " ")}
                  </button>
                ))}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-950/60 text-slate-400 font-mono text-[11px] uppercase border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Asset</th>
                    <th className="px-4 py-3">Shock A</th>
                    <th className="px-4 py-3">Shock B</th>
                    <th className="px-4 py-3">Delta Shock</th>
                    <th className="px-4 py-3">PnL A</th>
                    <th className="px-4 py-3">PnL B</th>
                    <th className="px-4 py-3">PnL Savings</th>
                    <th className="px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {filteredNodes.map((row) => (
                    <tr key={row.node_id} className="hover:bg-slate-900/50 transition">
                      <td className="px-4 py-3 font-sans font-bold text-white">{row.node_id}</td>
                      <td className="px-4 py-3 text-rose-400">{(row.shock_a * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-amber-400">{(row.shock_b * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-cyan-400 font-bold">
                        {(row.delta_shock * 100).toFixed(1)}%
                      </td>
                      <td className="px-4 py-3 text-slate-400">-${Math.abs(row.pnl_a).toLocaleString()}</td>
                      <td className="px-4 py-3 text-slate-300">-${Math.abs(row.pnl_b).toLocaleString()}</td>
                      <td className="px-4 py-3 font-bold text-emerald-400">
                        {row.delta_pnl >= 0 ? `+$${row.delta_pnl.toLocaleString()}` : `-$${Math.abs(row.delta_pnl).toLocaleString()}`}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            row.status === "DE_RISKED"
                              ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800/60"
                              : row.status === "AMPLIFIED"
                              ? "bg-rose-950/80 text-rose-400 border border-rose-800/60"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
