"use client";

import React, { useState, useEffect } from "react";
import {
  GitFork,
  ArrowRight,
  TrendingUp,
  DollarSign,
  ShieldCheck,
  Zap,
  RefreshCw,
  Layers,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5051";

interface MutationItem {
  id: string;
  enabled: boolean;
  mutation_type: "SEVER_EDGE" | "REWEIGHT_EDGE" | "ADD_EDGE";
  source_id: string;
  target_id: string;
  new_weight: number;
  capex_cost: number;
  lead_time_months: number;
  rationale: string;
}

interface MutationEvaluationResult {
  mutation_name: string;
  total_capex: number;
  baseline_pnl: number;
  mutated_pnl: number;
  avoided_loss: number;
  resilience_roi: number;
  regulatory_capital_relief: number;
  cvar_relief_pct: number;
  asset_pnl_deltas: Record<string, number>;
}

const DEFAULT_MUTATIONS: MutationItem[] = [
  {
    id: "mut-1",
    enabled: true,
    mutation_type: "REWEIGHT_EDGE",
    source_id: "TSM",
    target_id: "NVDA",
    new_weight: 0.15,
    capex_cost: 2500000,
    lead_time_months: 12,
    rationale: "Re-allocate 60% packaging to TSMC Fab 21 in Phoenix, Arizona",
  },
  {
    id: "mut-2",
    enabled: true,
    mutation_type: "ADD_EDGE",
    source_id: "INTC",
    target_id: "NVDA",
    new_weight: 0.20,
    capex_cost: 1200000,
    lead_time_months: 8,
    rationale: "Secondary foundry qualification with Intel Foundry Services",
  },
  {
    id: "mut-3",
    enabled: false,
    mutation_type: "SEVER_EDGE",
    source_id: "TSM",
    target_id: "AAPL",
    new_weight: 0.0,
    capex_cost: 4000000,
    lead_time_months: 18,
    rationale: "Complete diversification to domestic US & European foundries",
  },
];

export default function SupplyChainMutationStudio() {
  const [mutations, setMutations] = useState<MutationItem[]>(DEFAULT_MUTATIONS);
  const [mutationName, setMutationName] = useState<string>("Taiwan Decoupling & Arizona Dual-Sourcing");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [result, setResult] = useState<MutationEvaluationResult | null>(null);

  const toggleMutation = (id: string) => {
    setMutations((prev) =>
      prev.map((m) => (m.id === id ? { ...m, enabled: !m.enabled } : m))
    );
  };

  const removeMutation = (id: string) => {
    setMutations((prev) => prev.filter((m) => m.id !== id));
  };

  const evaluateMutations = async () => {
    setIsLoading(true);
    const activeMutations = mutations
      .filter((m) => m.enabled)
      .map(({ mutation_type, source_id, target_id, new_weight, capex_cost, lead_time_months, rationale }) => ({
        mutation_type,
        source_id,
        target_id,
        new_weight,
        capex_cost,
        lead_time_months,
        rationale,
      }));

    try {
      const res = await fetch(`${API_BASE}/api/v1/mutation/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mutation_name: mutationName,
          mutations: activeMutations,
          base_shocks: { TSM: -0.40, NVDA: -0.35, AAPL: -0.28, F: -0.22 },
          positions: { TSM: 20000000, NVDA: 25000000, AAPL: 20000000, F: 10000000 },
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch (e) {
      console.error("Mutation evaluation failed:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    evaluateMutations();
  }, []);

  const formatCurrency = (val: number) => {
    const absVal = Math.abs(val);
    const sign = val < 0 ? "-" : "";
    if (absVal >= 1e9) return `${sign}$${(absVal / 1e9).toFixed(2)}B`;
    if (absVal >= 1e6) return `${sign}$${(absVal / 1e6).toFixed(2)}M`;
    if (absVal >= 1e3) return `${sign}$${(absVal / 1e3).toFixed(1)}k`;
    return `${sign}$${absVal.toLocaleString()}`;
  };

  return (
    <div className="space-y-6">
      {/* Studio Banner */}
      <div className="bg-[#0b101b] border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="p-2 rounded-lg bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                <GitFork className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">
                What-If Supply Chain Graph Mutation Studio
              </h2>
            </div>
            <p className="text-xs text-slate-400 max-w-3xl">
              Model strategic network topology interventions (e.g. severing single-point dependencies, reweighting to dual-sourcing foundries, or qualifying new vendors) and measure their{" "}
              <strong className="text-emerald-300">Resilience ROI (&Delta;PnL / CapEx)</strong> and regulatory capital relief.
            </p>
          </div>

          <button
            onClick={evaluateMutations}
            disabled={isLoading}
            className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            <span>{isLoading ? "Evaluating ROI..." : "Evaluate Interventions"}</span>
          </button>
        </div>
      </div>

      {/* KPI ROI Grid */}
      {result && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#0b101b] border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Resilience ROI</span>
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400">
              {result.resilience_roi.toFixed(2)}x
            </div>
            <div className="text-[11px] text-slate-400 mt-1 font-mono">
              Return on Resilience Investment
            </div>
          </div>

          <div className="bg-[#0b101b] border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Avoided Stress Loss (&Delta;PnL)</span>
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-cyan-400">
              +{formatCurrency(result.avoided_loss)}
            </div>
            <div className="text-[11px] text-slate-400 mt-1 font-mono">
              From {formatCurrency(result.baseline_pnl)} &rarr; {formatCurrency(result.mutated_pnl)}
            </div>
          </div>

          <div className="bg-[#0b101b] border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Required CapEx Investment</span>
              <DollarSign className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-400">
              {formatCurrency(result.total_capex)}
            </div>
            <div className="text-[11px] text-slate-400 mt-1 font-mono">
              Foundry qualification &amp; logistics tooling
            </div>
          </div>

          <div className="bg-[#0b101b] border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Reg Capital Relief</span>
              <Zap className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-purple-400">
              {formatCurrency(result.regulatory_capital_relief)}
            </div>
            <div className="text-[11px] text-slate-400 mt-1 font-mono">
              CVaR Relief: <span className="text-emerald-400 font-bold">+{result.cvar_relief_pct.toFixed(1)}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Mutation Interventions Table */}
      <div className="bg-[#0b101b] border border-slate-800 rounded-2xl overflow-hidden">
        <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Network Intervention Registry
            </h3>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            {mutations.filter((m) => m.enabled).length} of {mutations.length} Active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Action</th>
                <th className="px-4 py-2.5">Source &rarr; Target</th>
                <th className="px-4 py-2.5 text-right">New Weight</th>
                <th className="px-4 py-2.5 text-right">CapEx ($)</th>
                <th className="px-4 py-2.5 text-right">Lead Time</th>
                <th className="px-4 py-2.5">Strategic Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {mutations.map((m) => (
                <tr key={m.id} className="hover:bg-slate-900/40 transition">
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={m.enabled}
                      onChange={() => toggleMutation(m.id)}
                      className="rounded accent-emerald-500 cursor-pointer"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        m.mutation_type === "SEVER_EDGE"
                          ? "bg-rose-950/80 text-rose-400 border border-rose-800/60"
                          : m.mutation_type === "ADD_EDGE"
                          ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800/60"
                          : "bg-cyan-950/80 text-cyan-400 border border-cyan-800/60"
                      }`}
                    >
                      {m.mutation_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-bold text-white flex items-center space-x-1.5">
                    <span className="text-slate-300">{m.source_id}</span>
                    <ArrowRight className="w-3 h-3 text-slate-500" />
                    <span className="text-cyan-400">{m.target_id}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {(m.new_weight * 100).toFixed(0)}%
                  </td>
                  <td className="px-4 py-3 text-right text-amber-400">
                    {formatCurrency(m.capex_cost)}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-400">
                    {m.lead_time_months}m
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-[11px] truncate max-w-xs">
                    {m.rationale}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Asset-by-Asset Avoided Loss Breakdown */}
      {result && result.asset_pnl_deltas && (
        <div className="bg-[#0b101b] border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Asset Avoided Loss Breakdown (&Delta;Loss Recovered)
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">
              Comparing Baseline vs Mutated Contagion Propagation
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {Object.entries(result.asset_pnl_deltas).map(([asset, delta]) => (
              <div key={asset} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="text-[11px] font-bold text-slate-300 font-mono">{asset}</div>
                <div className="text-lg font-bold font-mono text-emerald-400 mt-1">
                  +{formatCurrency(delta)}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
                  Reduced exposure via dual-sourcing
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
