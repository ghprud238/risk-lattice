"use client";

import React from "react";
import { TrendingDown, ShieldAlert, GitCommit, ArrowRight, Activity, Percent } from "lucide-react";

interface PnLWaterfallProps {
  portfolioPnl: {
    hop1_pnl: number;
    hop2_pnl: number;
    hop3_4_pnl: number;
    total_pnl: number;
  } | null;
  riskMetrics: {
    var_99: number;
    cvar_99: number;
    gaussian_var_99: number;
    copula_to_gaussian_ratio: number;
  } | null;
  criticalPaths: string[][];
  topDrawdowns: Array<{
    node_id: string;
    name: string;
    cumulative_shock: number;
    distress_multiplier: number;
    sector: string;
  }>;
}

export default function PnLWaterfall({
  portfolioPnl,
  riskMetrics,
  criticalPaths,
  topDrawdowns
}: PnLWaterfallProps) {
  if (!portfolioPnl) {
    return (
      <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-8 text-center text-slate-500 text-xs font-mono">
        No active stress simulation. Run a shock scenario to view the multi-hop PnL waterfall.
      </div>
    );
  }

  const hop1Pct = (portfolioPnl.hop1_pnl * 100).toFixed(2);
  const hop2Pct = (portfolioPnl.hop2_pnl * 100).toFixed(2);
  const hop3Pct = (portfolioPnl.hop3_4_pnl * 100).toFixed(2);
  const totalPct = (portfolioPnl.total_pnl * 100).toFixed(2);

  return (
    <div className="space-y-4">
      {/* 4 Waterfall Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-4 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>1st-Order (Direct Macro)</span>
            <Activity className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div className="text-xl font-bold font-mono text-blue-400">
            {portfolioPnl.hop1_pnl > 0 ? `+${hop1Pct}%` : `${hop1Pct}%`}
          </div>
          <p className="text-[10px] text-slate-400 mt-1">Direct factor beta transmission</p>
        </div>

        <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-4 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>2nd-Order (Tier-1 Suppliers)</span>
            <GitCommit className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-xl font-bold font-mono text-amber-400">
            {portfolioPnl.hop2_pnl > 0 ? `+${hop2Pct}%` : `${hop2Pct}%`}
          </div>
          <p className="text-[10px] text-slate-400 mt-1">Supplier/customer coupling shock</p>
        </div>

        <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-4 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>3rd/4th-Order (Contagion)</span>
            <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-xl font-bold font-mono text-rose-400">
            {portfolioPnl.hop3_4_pnl > 0 ? `+${hop3Pct}%` : `${hop3Pct}%`}
          </div>
          <p className="text-[10px] text-slate-400 mt-1">Non-linear network cascading</p>
        </div>

        <div className="bg-gradient-to-br from-red-950/60 to-slate-900 rounded-xl border border-red-800/60 p-4 shadow-lg">
          <div className="flex items-center justify-between text-slate-300 text-xs mb-1">
            <span className="font-bold">Total Simulated PnL</span>
            <Percent className="w-3.5 h-3.5 text-red-400" />
          </div>
          <div className="text-xl font-extrabold font-mono text-red-400">
            {portfolioPnl.total_pnl > 0 ? `+${totalPct}%` : `${totalPct}%`}
          </div>
          <p className="text-[10px] text-slate-400 mt-1">Audit: Hop1 + Hop2 + Hop3_4</p>
        </div>
      </div>

      {/* Tail Risk Copula vs Gaussian VaR Comparison Bar */}
      {riskMetrics && (
        <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-4 shadow-lg flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-red-950/80 border border-red-800/80 text-red-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-100 uppercase tracking-wide">
                10,000-Path Student-t Copula Monte Carlo Tail Risk
              </h4>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Evaluates heavy-tail non-linear dependency (ν = 4.0, PCG64 Seed = 42)
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-6 text-xs font-mono">
            <div>
              <span className="text-slate-400 block text-[10px]">99% Student-t CVaR:</span>
              <span className="text-sm font-bold text-red-400">
                {(riskMetrics.cvar_99 * 100).toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">60d Gaussian VaR:</span>
              <span className="text-sm font-semibold text-slate-300">
                {(riskMetrics.gaussian_var_99 * 100).toFixed(2)}%
              </span>
            </div>
            <div className="pl-3 border-l border-slate-800">
              <span className="text-slate-400 block text-[10px]">Tail Amplification:</span>
              <span className="text-sm font-bold text-amber-400">
                {riskMetrics.copula_to_gaussian_ratio}x
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Critical Contagion Transmission Paths & Top Holdings Drawdowns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Critical Paths */}
        <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-3.5 shadow-lg">
          <div className="flex items-center space-x-2 mb-2.5">
            <GitCommit className="w-4 h-4 text-cyan-400" />
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
              Critical Contagion Transmission Paths
            </h4>
          </div>
          {criticalPaths.length > 0 ? (
            <div className="space-y-2">
              {criticalPaths.slice(0, 4).map((path, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/80 rounded-lg p-2 border border-slate-800 flex items-center flex-wrap gap-1.5 text-[11px] font-mono text-slate-300"
                >
                  <span className="text-slate-500 font-bold mr-1">#{idx + 1}</span>
                  {path.map((node, nIdx) => (
                    <React.Fragment key={nIdx}>
                      <span className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 font-semibold border border-slate-700">
                        {node}
                      </span>
                      {nIdx < path.length - 1 && (
                        <ArrowRight className="w-3 h-3 text-slate-500" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">No multi-hop transmission chains detected.</p>
          )}
        </div>

        {/* Top Impacted Holdings */}
        <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-3.5 shadow-lg">
          <div className="flex items-center space-x-2 mb-2.5">
            <TrendingDown className="w-4 h-4 text-red-400" />
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
              Top Impacted Portfolio Holdings
            </h4>
          </div>
          <div className="space-y-1.5">
            {topDrawdowns.slice(0, 4).map((item, idx) => (
              <div
                key={idx}
                className="bg-slate-950/80 rounded-lg p-2 border border-slate-800 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-200 font-mono">{item.node_id}</span>
                    <span className="text-[10px] text-slate-400 truncate max-w-[130px]">
                      {item.name}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500">{item.sector}</span>
                </div>

                <div className="text-right font-mono">
                  <div className="font-bold text-red-400">
                    {(item.cumulative_shock * 100).toFixed(1)}%
                  </div>
                  {item.distress_multiplier > 1.0 && (
                    <span className="text-[10px] text-amber-400">
                      λ = {item.distress_multiplier.toFixed(2)}x
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
