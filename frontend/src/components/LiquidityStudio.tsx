"use client";

import React, { useState, useEffect } from "react";
import {
  Coins,
  TrendingDown,
  Flame,
  ShieldAlert,
  RefreshCw,
  Activity,
  Layers,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5051";

interface AssetImpact {
  asset_id: string;
  liquidated_notional: number;
  adv_30d: number;
  bid_ask_spread_bps: number;
  temporary_impact_pct: number;
  permanent_impact_pct: number;
  total_slippage_pct: number;
  market_impact_loss: number;
  days_to_liquidate: number;
}

interface MarginSummary {
  gross_derivative_notional: number;
  initial_margin_requirement: number;
  variation_margin_call: number;
  total_liquidity_drain: number;
  available_unencumbered_cash: number;
  net_cash_deficit: number;
  days_to_cash_exhaustion: number;
  post_stress_lcr_pct: number;
}

interface LiquiditySimulationData {
  total_notional_liquidated: number;
  total_market_impact_loss: number;
  blended_price_discount_pct: number;
  fire_sale_contagion_multiplier: number;
  margin_summary: MarginSummary;
  asset_impacts: AssetImpact[];
}

export default function LiquidityStudio() {
  const [liquidationPct, setLiquidationPct] = useState<number>(0.20);
  const [participationRate, setParticipationRate] = useState<number>(0.15);
  const [fundCash, setFundCash] = useState<number>(15000000);
  const [derivativeNotional, setDerivativeNotional] = useState<number>(150000000);
  const [unhedgedPnl, setUnhedgedPnl] = useState<number>(-23450000);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [data, setData] = useState<LiquiditySimulationData | null>(null);

  const runSimulation = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/liquidity/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          liquidation_pct: liquidationPct,
          participation_rate: participationRate,
          fund_unencumbered_cash: fundCash,
          portfolio_unhedged_pnl: unhedgedPnl,
          gross_derivative_notional: derivativeNotional,
        }),
      });
      if (res.ok) {
        const result = await res.json();
        setData(result);
      }
    } catch (e) {
      console.error("Liquidity simulation failed:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
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
      {/* Studio Header & Theoretical Formulation Banner */}
      <div className="bg-[#0b101b] border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="p-2 rounded-lg bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
                <Coins className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">
                Endogenous Market Impact &amp; Liquidity Spiral Studio
              </h2>
            </div>
            <p className="text-xs text-slate-400 max-w-3xl">
              Simulates nonlinear execution slippage via the <strong className="text-cyan-300">Almgren-Chriss (2000)</strong> market impact model, 
              accounting for bid-ask blowout, fire-sale feedback loops (<span className="font-mono text-amber-400">&xi;</span>), and ISDA SIMM derivative margin calls.
            </p>
          </div>

          <button
            onClick={runSimulation}
            disabled={isLoading}
            className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            <span>{isLoading ? "Simulating Liquidation..." : "Recompute Impact"}</span>
          </button>
        </div>

        {/* Parameter Sliders */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6 pt-5 border-t border-slate-800/80">
          <div className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-300">Liquidation Volume</span>
              <span className="text-xs font-mono font-bold text-cyan-400">
                {(liquidationPct * 100).toFixed(0)}% Portfolio
              </span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.50"
              step="0.05"
              value={liquidationPct}
              onChange={(e) => setLiquidationPct(parseFloat(e.target.value))}
              className="w-full accent-cyan-400 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
              <span>5%</span>
              <span>25%</span>
              <span>50%</span>
            </div>
          </div>

          <div className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-300">Participation Rate (&rho;)</span>
              <span className="text-xs font-mono font-bold text-cyan-400">
                {(participationRate * 100).toFixed(0)}% of ADV
              </span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.30"
              step="0.05"
              value={participationRate}
              onChange={(e) => setParticipationRate(parseFloat(e.target.value))}
              className="w-full accent-cyan-400 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
              <span>5% (Gentle)</span>
              <span>15% (Typical)</span>
              <span>30% (Aggressive)</span>
            </div>
          </div>

          <div className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-300">Unencumbered Cash</span>
              <span className="text-xs font-mono font-bold text-emerald-400">
                {formatCurrency(fundCash)}
              </span>
            </div>
            <input
              type="range"
              min="5000000"
              max="50000000"
              step="5000000"
              value={fundCash}
              onChange={(e) => setFundCash(parseFloat(e.target.value))}
              className="w-full accent-emerald-400 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
              <span>$5M</span>
              <span>$25M</span>
              <span>$50M</span>
            </div>
          </div>

          <div className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-300">Gross Derivatives</span>
              <span className="text-xs font-mono font-bold text-purple-400">
                {formatCurrency(derivativeNotional)}
              </span>
            </div>
            <input
              type="range"
              min="50000000"
              max="300000000"
              step="25000000"
              value={derivativeNotional}
              onChange={(e) => setDerivativeNotional(parseFloat(e.target.value))}
              className="w-full accent-purple-400 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
              <span>$50M</span>
              <span>$150M</span>
              <span>$300M</span>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#0b101b] border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Total Notional Liquidated</span>
              <Coins className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-xl font-bold font-mono text-white">
              {formatCurrency(data.total_notional_liquidated)}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Across {(data.asset_impacts || []).length} institutional equity &amp; bond holdings
            </div>
          </div>

          <div className="bg-[#0b101b] border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Execution Slippage Loss</span>
              <TrendingDown className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-xl font-bold font-mono text-rose-400">
              {formatCurrency(data.total_market_impact_loss)}
            </div>
            <div className="text-[11px] text-slate-400 mt-1 font-mono">
              Discount: <span className="text-rose-300 font-bold">{data.blended_price_discount_pct.toFixed(2)}%</span> vs Mid-Market
            </div>
          </div>

          <div className="bg-[#0b101b] border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Fire-Sale Feedback Multiplier (&xi;)</span>
              <Flame className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-xl font-bold font-mono text-amber-400">
              {data.fire_sale_contagion_multiplier.toFixed(2)}x
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Amplified by peer distress &amp; volume crowding
            </div>
          </div>

          <div className="bg-[#0b101b] border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Post-Stress LCR</span>
              <ShieldAlert className="w-4 h-4 text-emerald-400" />
            </div>
            <div className={`text-xl font-bold font-mono ${data.margin_summary.post_stress_lcr_pct >= 100 ? "text-emerald-400" : "text-rose-400"}`}>
              {data.margin_summary.post_stress_lcr_pct.toFixed(1)}%
            </div>
            <div className="text-[11px] text-slate-400 mt-1 font-mono">
              Cash Exhaustion: <span className="font-bold text-white">{data.margin_summary.days_to_cash_exhaustion.toFixed(1)} Days</span>
            </div>
          </div>
        </div>
      )}

      {/* Margin Call & Derivative Drainage Card */}
      {data && (
        <div className="bg-[#0b101b] border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-purple-400" />
              <h3 className="text-sm font-bold text-white">
                ISDA SIMM Margin Call &amp; Cash Buffer Analysis
              </h3>
            </div>
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-purple-950/80 text-purple-400 border border-purple-800/60">
              Reg Margin Period of Risk = 10 Days
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-[11px] text-slate-400">Initial Margin (IM) Req</div>
              <div className="text-base font-bold font-mono text-slate-200 mt-1">
                {formatCurrency(data.margin_summary.initial_margin_requirement)}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
                12% baseline on derivatives
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-[11px] text-slate-400">Variation Margin (VM) Call</div>
              <div className="text-base font-bold font-mono text-rose-400 mt-1">
                {formatCurrency(data.margin_summary.variation_margin_call)}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
                Triggered by spot drawdown
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-[11px] text-slate-400">Total Liquidity Drain</div>
              <div className="text-base font-bold font-mono text-amber-400 mt-1">
                {formatCurrency(data.margin_summary.total_liquidity_drain)}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
                Execution slippage + Margin call
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-[11px] text-slate-400">Net Cash Position</div>
              <div className={`text-base font-bold font-mono mt-1 ${data.margin_summary.net_cash_deficit > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                {data.margin_summary.net_cash_deficit > 0
                  ? `Deficit: ${formatCurrency(data.margin_summary.net_cash_deficit)}`
                  : `Surplus: ${formatCurrency(data.margin_summary.available_unencumbered_cash - data.margin_summary.total_liquidity_drain)}`}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
                {data.margin_summary.net_cash_deficit > 0 ? "⚠️ Capital call required" : "✓ Cash buffer sufficient"}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Asset-by-Asset Impact Breakdown Table */}
      {data && (
        <div className="bg-[#0b101b] border border-slate-800 rounded-2xl overflow-hidden">
          <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Almgren-Chriss Asset Impact Breakdown
              </h3>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              I_temp = &eta;&sigma;&radic;(Vol/ADV) &bull; I_perm = &gamma;(Vol/ADV)
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-900/80 text-slate-400 text-[10px] uppercase border-b border-slate-800">
                <tr>
                  <th className="px-4 py-2.5">Asset ID</th>
                  <th className="px-4 py-2.5 text-right">Liquidated Notional</th>
                  <th className="px-4 py-2.5 text-right">30d ADV</th>
                  <th className="px-4 py-2.5 text-right">Spread Blowout</th>
                  <th className="px-4 py-2.5 text-right">Temp Impact</th>
                  <th className="px-4 py-2.5 text-right">Perm Impact</th>
                  <th className="px-4 py-2.5 text-right">Total Slippage</th>
                  <th className="px-4 py-2.5 text-right">Execution Loss</th>
                  <th className="px-4 py-2.5 text-right">Est. Days</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {(data.asset_impacts || []).map((asset) => (
                  <tr key={asset.asset_id} className="hover:bg-slate-900/40 transition">
                    <td className="px-4 py-3 font-bold text-white flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                      <span>{asset.asset_id}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {formatCurrency(asset.liquidated_notional)}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-400">
                      {formatCurrency(asset.adv_30d)}
                    </td>
                    <td className="px-4 py-3 text-right text-amber-400">
                      {asset.bid_ask_spread_bps.toFixed(0)} bps
                    </td>
                    <td className="px-4 py-3 text-right text-rose-300">
                      {asset.temporary_impact_pct.toFixed(2)}%
                    </td>
                    <td className="px-4 py-3 text-right text-rose-400">
                      {asset.permanent_impact_pct.toFixed(2)}%
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-rose-400">
                      {asset.total_slippage_pct.toFixed(2)}%
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-rose-400">
                      {formatCurrency(asset.market_impact_loss)}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-400 font-bold">
                      {asset.days_to_liquidate.toFixed(1)}d
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
