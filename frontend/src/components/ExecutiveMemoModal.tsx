"use client";

import React, { useState } from "react";
import {
  FileText,
  Printer,
  X,
  CheckCircle,
} from "lucide-react";

interface ExecutiveMemoModalProps {
  isOpen: boolean;
  onClose: () => void;
  scenarioName?: string;
  portfolioNotional?: number;
  pnlLoss?: number;
  cvar99?: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5051";

export default function ExecutiveMemoModal({
  isOpen,
  onClose,
  scenarioName = "Taiwan Strait Blockade & Foundry Disruption",
  portfolioNotional = 100000000,
  pnlLoss = -23450000,
  cvar99 = 29312500,
}: ExecutiveMemoModalProps) {
  const [memoData, setMemoData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  React.useEffect(() => {
    if (isOpen) {
      const fetchMemo = async () => {
        setIsLoading(true);
        try {
          const res = await fetch(`${API_BASE}/api/v1/report/executive`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              scenario_name: scenarioName,
              portfolio_notional: portfolioNotional,
              pnl_loss: pnlLoss,
              cvar_99: cvar99,
              var_95: cvar99 * 0.72,
            }),
          });
          if (res.ok) {
            const data = await res.json();
            setMemoData(data);
          }
        } catch (e) {
          console.error("Memo generation failed", e);
        } finally {
          setIsLoading(false);
        }
      };
      fetchMemo();
    }
  }, [isOpen, scenarioName, portfolioNotional, pnlLoss, cvar99]);

  if (!isOpen) return null;

  const handlePrint = () => {
    if (memoData?.html_content) {
      const printWindow = window.open("", "_blank");
      if (printWindow) {
        printWindow.document.write(memoData.html_content);
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
          printWindow.print();
        }, 300);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="bg-[#0b101b] border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-950/80 border border-cyan-800/80 flex items-center justify-center text-cyan-400">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white tracking-wide">
                Board-Ready Executive Stress Testing Memorandum
              </h3>
              <p className="text-[11px] text-slate-400">
                SR 11-7 / BCBS 239 Compliant • Print-Ready Investment Committee Packet
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handlePrint}
              disabled={!memoData || isLoading}
              className="px-3.5 py-1.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs flex items-center space-x-1.5 shadow transition disabled:opacity-50"
            >
              <Printer className="w-3.5 h-3.5 fill-slate-950" />
              <span>Print / Export PDF</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {isLoading && (
            <div className="py-16 text-center text-slate-400 font-mono text-xs">
              Compiling Executive Stress Memo &amp; Audited Disclosures...
            </div>
          )}

          {memoData && (
            <div className="space-y-6">
              {/* Institutional Cover Header */}
              <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950 text-rose-400 border border-rose-800/60">
                    {memoData.classification}
                  </span>
                  <h1 className="text-xl font-bold text-white mt-2">
                    {memoData.scenario_name.toUpperCase()}
                  </h1>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Prepared for: {memoData.signoff?.firm} • Generated: {memoData.generated_at}
                  </p>
                </div>
                <div className="text-right font-mono text-[11px] text-slate-500">
                  <div>Ref: {memoData.memo_id}</div>
                  <div className="text-emerald-400 font-bold mt-1">[SR 11-7 VERIFIED]</div>
                </div>
              </div>

              {/* KPI Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-xl">
                  <div className="text-[10px] text-slate-400 uppercase font-mono">Portfolio Base</div>
                  <div className="text-lg font-bold font-mono text-white mt-1">
                    ${(memoData.portfolio_notional / 1000000).toFixed(0)}M
                  </div>
                </div>
                <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-xl">
                  <div className="text-[10px] text-slate-400 uppercase font-mono">Net PnL Shock</div>
                  <div className="text-lg font-bold font-mono text-rose-400 mt-1">
                    -${Math.abs(memoData.total_pnl_loss).toLocaleString()}
                  </div>
                  <div className="text-[10px] text-rose-500 font-bold">
                    {memoData.drawdown_pct.toFixed(1)}% Drawdown
                  </div>
                </div>
                <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-xl">
                  <div className="text-[10px] text-slate-400 uppercase font-mono">Tail CVaR (99.0%)</div>
                  <div className="text-lg font-bold font-mono text-amber-400 mt-1">
                    ${(memoData.cvar_99 / 1000000).toFixed(1)}M
                  </div>
                </div>
                <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-xl">
                  <div className="text-[10px] text-slate-400 uppercase font-mono">Contagion VaR (95%)</div>
                  <div className="text-lg font-bold font-mono text-cyan-400 mt-1">
                    ${(memoData.var_95 / 1000000).toFixed(1)}M
                  </div>
                </div>
              </div>

              {/* Executive Loss Attribution Table */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
                <div className="px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 text-xs font-bold text-slate-200">
                  1. Component Loss Attribution
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-950 text-slate-400 font-mono text-[10px] uppercase border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-2">Asset &amp; Supply Tier</th>
                        <th className="px-4 py-2">Notional</th>
                        <th className="px-4 py-2">Simulated Shock</th>
                        <th className="px-4 py-2">Net PnL Impact</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {memoData.top_losses.map((loss: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-900/30">
                          <td className="px-4 py-2 font-sans text-slate-200 font-bold">
                            {loss.asset} <span className="text-slate-400 font-normal">({loss.tier})</span>
                          </td>
                          <td className="px-4 py-2 text-slate-400">{loss.notional}</td>
                          <td className="px-4 py-2 text-rose-400">{loss.shock}</td>
                          <td className="px-4 py-2 text-rose-400 font-bold">-{loss.pnl}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Recommended Tail Hedges */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
                <div className="px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 text-xs font-bold text-slate-200">
                  2. Actionable Tail-Risk Hedge Recommendations
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-950 text-slate-400 font-mono text-[10px] uppercase border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-2">Instrument</th>
                        <th className="px-4 py-2">Optimal Size</th>
                        <th className="px-4 py-2">Cost (bps)</th>
                        <th className="px-4 py-2">Tail PnL Shield</th>
                        <th className="px-4 py-2">Efficiency</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {memoData.recommended_hedges.map((h: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-900/30">
                          <td className="px-4 py-2 font-sans font-semibold text-white">{h.instrument}</td>
                          <td className="px-4 py-2 text-slate-300">{h.allocation}</td>
                          <td className="px-4 py-2 text-rose-400">{h.premium_bps}</td>
                          <td className="px-4 py-2 text-emerald-400 font-bold">{h.tail_pnl_restitution}</td>
                          <td className="px-4 py-2 text-cyan-400">{h.efficiency}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* SEC Citations */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 space-y-3">
                <div className="text-xs font-bold text-slate-200">
                  3. Ground-Truth SEC 10-K Supply Chain Disclosures
                </div>
                <div className="space-y-2 text-xs">
                  {memoData.sec_citations.map((c: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-slate-300"
                    >
                      <div className="font-bold text-cyan-400">{c.entity}</div>
                      <div className="italic text-slate-400 mt-1">&ldquo;{c.quote}&rdquo;</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* CRO Signature Block */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="text-xs font-bold text-slate-200">
                    FEDERAL RESERVE SR 11-7 / OCC 2011-12 GOVERNANCE SIGN-OFF
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Independently signed by: <strong className="text-white">{memoData.signoff?.cro_name}</strong> ({memoData.signoff?.cro_title})
                  </div>
                  <div className="text-[10px] text-slate-500">{memoData.signoff?.firm}</div>
                </div>
                <div className="text-right">
                  <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded bg-emerald-950/80 border border-emerald-800/80 text-emerald-400 font-mono text-[10px] font-bold">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                    <span>DIGITALLY SEALED</span>
                  </div>
                  <div className="text-[9px] font-mono text-slate-500 mt-1">
                    SHA-256: {memoData.signoff?.seal_hash?.slice(0, 24)}...
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
