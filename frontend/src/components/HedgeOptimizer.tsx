"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  Zap,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";

interface HedgeRecommendation {
  candidate_id: string;
  instrument_name: string;
  target_node: string;
  action: string;
  allocated_notional: number;
  estimated_cost: number;
  pnl_protection: number;
  description: string;
}

interface FrontierPoint {
  budget: number;
  protection_pnl: number;
  cvar_reduction_pct: number;
}

interface HedgeOptimizerProps {
  unhedgedPnl?: number;
  nodeShocks?: Record<string, number>;
  portfolioNotional?: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5051";

export default function HedgeOptimizer({
  unhedgedPnl = -23450000,
  nodeShocks = { TSM: -0.40, NVDA: -0.32, AAPL: -0.26, F: -0.22 },
  portfolioNotional = 100000000,
}: HedgeOptimizerProps) {
  const [activeSubTab, setActiveSubTab] = useState<"hedge" | "reverse">("hedge");

  // Hedge Optimizer State
  const [budgetLimit, setBudgetLimit] = useState<number>(500000);
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [optimizationResult, setOptimizationResult] = useState<{
    initial_pnl: number;
    hedged_pnl: number;
    pnl_improvement: number;
    total_hedge_cost: number;
    initial_cvar_99: number;
    hedged_cvar_99: number;
    cvar_reduction_pct: number;
    recommendations: HedgeRecommendation[];
    efficient_frontier: FrontierPoint[];
  } | null>(null);

  // Reverse Stress State
  const [targetLossPct, setTargetLossPct] = useState<number>(20);
  const [isReverseSolving, setIsReverseSolving] = useState<boolean>(false);
  const [reverseResult, setReverseResult] = useState<{
    target_loss_pct: number;
    achieved_loss_pct: number;
    minimal_shocks: Record<string, number>;
    norm_l2: number;
    critical_factor: string;
    top_vulnerable_nodes: Array<{ factor: string; shock: number; loss_contribution_pct: number }>;
    iterations: number;
  } | null>(null);

  // Run SLSQP Convex Hedge Optimization
  const handleOptimize = async () => {
    setIsOptimizing(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/optimize/hedge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          portfolio_notional: portfolioNotional,
          unhedged_pnl: unhedgedPnl,
          node_shocks: nodeShocks,
          budget_limit: budgetLimit,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setOptimizationResult(data);
      }
    } catch (e) {
      console.error("Optimization failed", e);
    } finally {
      setIsOptimizing(false);
    }
  };

  // Run Inverse Solver for Reverse Stress Testing
  const handleReverseStress = async () => {
    setIsReverseSolving(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/stress/reverse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          portfolio_notional: portfolioNotional,
          target_loss_pct: targetLossPct / 100.0,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setReverseResult(data);
      }
    } catch (e) {
      console.error("Reverse stress solving failed", e);
    } finally {
      setIsReverseSolving(false);
    }
  };

  return (
    <div className="bg-[#0b101b] border border-slate-800 rounded-xl p-6 shadow-2xl space-y-6">
      {/* Sub-tab Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              Quantitative Hedge Optimizer &amp; Reverse Stress Studio
            </h2>
            <p className="text-xs text-slate-400">
              PRD Section 16 • SLSQP Capital-Efficient Tail Protection &amp; Inverse L2 Shock Solver
            </p>
          </div>
        </div>

        <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setActiveSubTab("hedge")}
            className={`px-3 py-1.5 rounded-lg font-medium transition ${
              activeSubTab === "hedge"
                ? "bg-cyan-500 text-slate-950 font-bold shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Tail-Risk Hedge Optimizer
          </button>
          <button
            onClick={() => setActiveSubTab("reverse")}
            className={`px-3 py-1.5 rounded-lg font-medium transition ${
              activeSubTab === "reverse"
                ? "bg-cyan-500 text-slate-950 font-bold shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Reverse Stress Testing
          </button>
        </div>
      </div>

      {/* Mode 1: Tail-Risk Hedge Optimizer */}
      {activeSubTab === "hedge" && (
        <div className="space-y-6">
          {/* Controls Bar */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-900/50 p-4 rounded-xl border border-slate-800">
            <div>
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>Hedge Premium Budget</span>
                <span className="font-mono text-cyan-400">${budgetLimit.toLocaleString()}</span>
              </label>
              <input
                type="range"
                min={100000}
                max={2000000}
                step={50000}
                value={budgetLimit}
                onChange={(e) => setBudgetLimit(Number(e.target.value))}
                className="w-full mt-2 accent-cyan-400"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1">
                <span>$100k (10 bps)</span>
                <span>$1M (100 bps)</span>
                <span>$2M (200 bps)</span>
              </div>
            </div>

            <div className="flex flex-col justify-center">
              <div className="text-[11px] text-slate-400">Target Unhedged Stress PnL</div>
              <div className="text-base font-bold font-mono text-rose-400">
                -${Math.abs(unhedgedPnl).toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-500 font-mono">
                Across {Object.keys(nodeShocks).length} direct &amp; propagated asset nodes
              </div>
            </div>

            <div className="flex items-center justify-end">
              <button
                onClick={handleOptimize}
                disabled={isOptimizing}
                className="w-full md:w-auto px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-cyan-950/50 flex items-center justify-center space-x-2 transition disabled:opacity-50"
              >
                {isOptimizing ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Zap className="w-4 h-4 fill-slate-950" />
                )}
                <span>{isOptimizing ? "Solving SLSQP..." : "Solve Optimal Basket"}</span>
              </button>
            </div>
          </div>

          {/* Results Display */}
          {optimizationResult && (
            <div className="space-y-6">
              {/* KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <div className="text-[11px] font-medium text-slate-400">Net PnL Improvement</div>
                  <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                    +${optimizationResult.pnl_improvement.toLocaleString()}
                  </div>
                  <div className="text-[10px] text-emerald-500 mt-0.5">
                    Hedged PnL: -${Math.abs(optimizationResult.hedged_pnl).toLocaleString()}
                  </div>
                </div>

                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <div className="text-[11px] font-medium text-slate-400">Total Premium Deployed</div>
                  <div className="text-xl font-bold font-mono text-cyan-400 mt-1">
                    ${optimizationResult.total_hedge_cost.toLocaleString()}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    {(optimizationResult.total_hedge_cost / portfolioNotional * 10000).toFixed(1)} bps of fund notional
                  </div>
                </div>

                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <div className="text-[11px] font-medium text-slate-400">Tail CVaR (99%) Shift</div>
                  <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                    -{optimizationResult.cvar_reduction_pct.toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    Down to ${optimizationResult.hedged_cvar_99.toLocaleString()}
                  </div>
                </div>

                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <div className="text-[11px] font-medium text-slate-400">Capital Efficiency</div>
                  <div className="text-xl font-bold font-mono text-amber-400 mt-1">
                    {(optimizationResult.pnl_improvement / Math.max(1, optimizationResult.total_hedge_cost)).toFixed(1)}x
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Payoff-to-premium ratio</div>
                </div>
              </div>

              {/* Recommended Allocations Table */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
                <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
                  <div className="text-xs font-bold text-slate-200">
                    Recommended Institutional Hedging Basket
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">
                    {optimizationResult.recommendations.length} Selected Candidates
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-950/60 text-slate-400 font-mono text-[11px] uppercase border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-3">Candidate / Instrument</th>
                        <th className="px-4 py-3">Target Node</th>
                        <th className="px-4 py-3">Action</th>
                        <th className="px-4 py-3">Optimal Notional</th>
                        <th className="px-4 py-3">Estimated Cost</th>
                        <th className="px-4 py-3">Tail PnL Shield</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {optimizationResult.recommendations.map((rec) => (
                        <tr key={rec.candidate_id} className="hover:bg-slate-900/50 transition">
                          <td className="px-4 py-3">
                            <div className="font-semibold text-white">{rec.candidate_id}</div>
                            <div className="text-[10px] text-slate-400">{rec.instrument_name}</div>
                          </td>
                          <td className="px-4 py-3 font-mono font-bold text-cyan-400">{rec.target_node}</td>
                          <td className="px-4 py-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                              {rec.action}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-mono text-slate-200">
                            ${rec.allocated_notional.toLocaleString()}
                          </td>
                          <td className="px-4 py-3 font-mono text-rose-400">
                            ${rec.estimated_cost.toLocaleString()}
                          </td>
                          <td className="px-4 py-3 font-mono font-bold text-emerald-400">
                            +${rec.pnl_protection.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Efficient Frontier Curve */}
              {optimizationResult.efficient_frontier?.length > 0 && (
                <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
                  <div className="text-xs font-bold text-slate-200 mb-3">
                    Efficient Frontier: Budget vs. CVaR Tail Protection
                  </div>
                  <div className="grid grid-cols-5 gap-2">
                    {optimizationResult.efficient_frontier.map((pt, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-center"
                      >
                        <div className="text-[10px] text-slate-400 font-mono">
                          ${(pt.budget / 1000).toFixed(0)}k Cost
                        </div>
                        <div className="text-base font-bold font-mono text-cyan-400 mt-1">
                          +{pt.cvar_reduction_pct.toFixed(0)}%
                        </div>
                        <div className="text-[9px] text-emerald-500 font-mono">
                          +${(pt.protection_pnl / 1000000).toFixed(1)}M PnL
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Mode 2: Reverse Stress Testing */}
      {activeSubTab === "reverse" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-900/50 p-4 rounded-xl border border-slate-800">
            <div>
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>Target Portfolio Loss Threshold</span>
                <span className="font-mono text-rose-400 font-bold">{targetLossPct}%</span>
              </label>
              <input
                type="range"
                min={5}
                max={50}
                step={5}
                value={targetLossPct}
                onChange={(e) => setTargetLossPct(Number(e.target.value))}
                className="w-full mt-2 accent-rose-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1">
                <span>5% ($5M)</span>
                <span>20% ($20M)</span>
                <span>50% ($50M)</span>
              </div>
            </div>

            <div className="flex flex-col justify-center">
              <div className="text-[11px] text-slate-400">Inverse Problem Formulation</div>
              <div className="text-xs font-mono text-slate-300 mt-1">
                min ||F||₂ subject to PnL_Loss(F) ≥ {targetLossPct}%
              </div>
              <div className="text-[10px] text-slate-500">
                Solves for the most probable macro/choke shock trigger
              </div>
            </div>

            <div className="flex items-center justify-end">
              <button
                onClick={handleReverseStress}
                disabled={isReverseSolving}
                className="w-full md:w-auto px-5 py-2.5 bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-rose-950/50 flex items-center justify-center space-x-2 transition disabled:opacity-50"
              >
                {isReverseSolving ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <AlertTriangle className="w-4 h-4" />
                )}
                <span>{isReverseSolving ? "Inverting Kernel..." : "Solve Minimal Breaking Point"}</span>
              </button>
            </div>
          </div>

          {reverseResult && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <div className="text-[11px] text-slate-400">Achieved Portfolio Drawdown</div>
                  <div className="text-xl font-bold font-mono text-rose-400 mt-1">
                    {(reverseResult.achieved_loss_pct * 100).toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-slate-500">
                    -${(reverseResult.achieved_loss_pct * portfolioNotional).toLocaleString()} loss
                  </div>
                </div>

                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <div className="text-[11px] text-slate-400">Critical Vulnerability Factor</div>
                  <div className="text-xl font-bold font-mono text-amber-400 mt-1">
                    {reverseResult.critical_factor}
                  </div>
                  <div className="text-[10px] text-slate-500">Highest marginal loss contribution</div>
                </div>

                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <div className="text-[11px] text-slate-400">Shock Vector L2 Norm</div>
                  <div className="text-xl font-bold font-mono text-cyan-400 mt-1">
                    {reverseResult.norm_l2.toFixed(4)}
                  </div>
                  <div className="text-[10px] text-slate-500">Minimal plausible Euclidean distance</div>
                </div>

                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <div className="text-[11px] text-slate-400">Solver Convergence</div>
                  <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                    {reverseResult.iterations} iters
                  </div>
                  <div className="text-[10px] text-emerald-500">SLSQP Karush-Kuhn-Tucker satisfied</div>
                </div>
              </div>

              {/* Minimal Shocks Table */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
                <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 text-xs font-bold text-slate-200">
                  Minimal Factor Shocks Required to Breach {targetLossPct}% Portfolio Loss
                </div>
                <div className="p-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  {Object.entries(reverseResult.minimal_shocks).map(([factor, shock]) => (
                    <div
                      key={factor}
                      className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex flex-col justify-between"
                    >
                      <div className="text-xs font-mono font-bold text-slate-300">{factor}</div>
                      <div className="text-lg font-mono font-bold text-rose-400 mt-1">
                        {(shock * 100).toFixed(1)}%
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">Minimal impulse</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
