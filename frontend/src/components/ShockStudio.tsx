"use client";

import React, { useState } from "react";
import { Play, Sparkles, Radio, Zap, Sliders, AlertTriangle } from "lucide-react";

interface ShockStudioProps {
  onSimulate: (prompt: string, directImpulses?: Record<string, number>) => Promise<void>;
  onStartSSEStream: (prompt: string, directImpulses?: Record<string, number>) => Promise<void>;
  isSimulating: boolean;
  streamingHop: { hop: number; label: string } | null;
}

const PRESET_SCENARIOS = [
  {
    title: "Synthetic Taiwan Foundry Halt",
    prompt: "Taiwan advanced wafer fab halt with severe shipping freight rate spike",
    defaults: { FOUNDRY_TW: -0.70, BALTIC_DRY: 1.80 }
  },
  {
    title: "2008 Liquidity & Credit Freeze",
    prompt: "Interbank credit freeze with high-yield option-adjusted spread blowout and SOFR rate spike",
    defaults: { HY_OAS: 0.085, SOFR_SPREAD: 0.035, VIX: 0.85 }
  },
  {
    title: "2020 Mobility & Oil Crash",
    prompt: "Global transit halt with Brent crude oil collapse and severe port congestion",
    defaults: { BRENT_CRUDE: -0.55, BALTIC_DRY: -0.48 }
  },
  {
    title: "2022 Duration Shock",
    prompt: "US 10-year real yield surge with rapid dollar appreciation causing tech valuation contraction",
    defaults: { US10Y_REAL: 0.026, DXY: 0.140 }
  }
];

export default function ShockStudio({
  onSimulate,
  onStartSSEStream,
  isSimulating,
  streamingHop
}: ShockStudioProps) {
  const [prompt, setPrompt] = useState(PRESET_SCENARIOS[0].prompt);
  const [factors, setFactors] = useState<Record<string, number>>({
    FOUNDRY_TW: -0.70,
    BALTIC_DRY: 1.80,
    US10Y_REAL: 0.0,
    BRENT_CRUDE: 0.0,
    HY_OAS: 0.0,
    SOFR_SPREAD: 0.0,
    VIX: 0.0
  });

  const handleSliderChange = (key: string, value: number) => {
    setFactors((prev) => ({ ...prev, [key]: value }));
  };

  const handleApplyPreset = (preset: typeof PRESET_SCENARIOS[0]) => {
    setPrompt(preset.prompt);
    setFactors({
      FOUNDRY_TW: preset.defaults.FOUNDRY_TW ?? 0.0,
      BALTIC_DRY: preset.defaults.BALTIC_DRY ?? 0.0,
      US10Y_REAL: preset.defaults.US10Y_REAL ?? 0.0,
      BRENT_CRUDE: preset.defaults.BRENT_CRUDE ?? 0.0,
      HY_OAS: preset.defaults.HY_OAS ?? 0.0,
      SOFR_SPREAD: preset.defaults.SOFR_SPREAD ?? 0.0,
      VIX: preset.defaults.VIX ?? 0.0
    });
  };

  const handleRunMath = () => {
    // Only pass non-zero slider impulses
    const active: Record<string, number> = {};
    for (const [k, v] of Object.entries(factors)) {
      if (Math.abs(v) > 0.001) active[k] = v;
    }
    onSimulate(prompt, active);
  };

  const handleRunStream = () => {
    const active: Record<string, number> = {};
    for (const [k, v] of Object.entries(factors)) {
      if (Math.abs(v) > 0.001) active[k] = v;
    }
    onStartSSEStream(prompt, active);
  };

  return (
    <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-5 shadow-xl space-y-4">
      {/* Title & Presets Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <Zap className="w-5 h-5 text-amber-400" />
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
            Shock Studio & Scenario Generator
          </h2>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {PRESET_SCENARIOS.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleApplyPreset(p)}
              className="text-[11px] px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 hover:border-slate-600 transition"
            >
              {p.title}
            </button>
          ))}
        </div>
      </div>

      {/* Natural Language Prompt Input */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
          <span>Natural-Language Shock Scenario Prompt</span>
          <span className="text-[11px] text-cyan-400 flex items-center">
            <Sparkles className="w-3 h-3 mr-1" />
            LiteLLM Semantic Translation
          </span>
        </label>
        <div className="relative">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Taiwan Strait maritime shipping blockade and sudden +250 bps real rate shock..."
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition shadow-inner font-mono"
          />
        </div>
      </div>

      {/* Factor Sliders Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
        <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
          <div className="flex justify-between text-[11px] font-mono text-slate-300 mb-1">
            <span className="text-amber-400">FOUNDRY_TW</span>
            <span>{(factors.FOUNDRY_TW * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="-0.95"
            max="0.50"
            step="0.05"
            value={factors.FOUNDRY_TW}
            onChange={(e) => handleSliderChange("FOUNDRY_TW", parseFloat(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
          />
        </div>

        <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
          <div className="flex justify-between text-[11px] font-mono text-slate-300 mb-1">
            <span className="text-purple-400">BALTIC_DRY</span>
            <span>{(factors.BALTIC_DRY * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="-0.80"
            max="2.00"
            step="0.10"
            value={factors.BALTIC_DRY}
            onChange={(e) => handleSliderChange("BALTIC_DRY", parseFloat(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
          />
        </div>

        <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
          <div className="flex justify-between text-[11px] font-mono text-slate-300 mb-1">
            <span className="text-purple-400">US10Y_REAL</span>
            <span>+{(factors.US10Y_REAL * 100).toFixed(1)}%</span>
          </div>
          <input
            type="range"
            min="-0.02"
            max="0.06"
            step="0.005"
            value={factors.US10Y_REAL}
            onChange={(e) => handleSliderChange("US10Y_REAL", parseFloat(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
          />
        </div>

        <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
          <div className="flex justify-between text-[11px] font-mono text-slate-300 mb-1">
            <span className="text-purple-400">BRENT_CRUDE</span>
            <span>{(factors.BRENT_CRUDE * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="-0.80"
            max="1.00"
            step="0.05"
            value={factors.BRENT_CRUDE}
            onChange={(e) => handleSliderChange("BRENT_CRUDE", parseFloat(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
          />
        </div>
      </div>

      {/* Action Execution Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
        <div className="flex items-center space-x-2">
          {streamingHop && (
            <div className="flex items-center space-x-2 bg-cyan-950/60 border border-cyan-800/80 px-3 py-1.5 rounded-lg text-xs text-cyan-300 animate-pulse">
              <Radio className="w-4 h-4 text-cyan-400 animate-spin" />
              <span className="font-mono font-medium">{streamingHop.label}</span>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleRunStream}
            disabled={isSimulating}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-cyan-500/40 font-semibold text-xs transition disabled:opacity-50"
          >
            <Radio className="w-3.5 h-3.5" />
            <span>Stream Hop Cascade (SSE)</span>
          </button>

          <button
            onClick={handleRunMath}
            disabled={isSimulating}
            className="flex items-center space-x-1.5 px-5 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{isSimulating ? "Computing..." : "Run Deterministic Shock Math"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
