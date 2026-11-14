"use client";

import React, { useState, useEffect } from "react";
import {
  Clock,
  Play,
  Pause,
  RotateCcw,
  AlertOctagon,
  AlertTriangle,
  Info,
  Calendar,
  TrendingDown,
  Warehouse,
} from "lucide-react";

interface Milestone {
  day: number;
  event_type: string;
  node_id: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  description: string;
}

interface TimelineStep {
  day: number;
  cumulative_pnl: number;
  drawdown_pct: number;
  cvar_99: number;
  active_nodes_count: number;
  node_shocks: Record<string, number>;
  inventory_levels: Record<string, number>;
  milestones: Milestone[];
}

interface TimelinePlayerProps {
  initialShocks?: Record<string, number>;
  portfolioNotional?: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5051";

const HORIZONS = [0, 7, 14, 30, 45, 60, 90];

export default function TimelinePlayer({
  initialShocks = { TSM: -0.40 },
  portfolioNotional = 100000000,
}: TimelinePlayerProps) {
  const [timelineData, setTimelineData] = useState<{
    initial_pnl: number;
    peak_drawdown_pnl: number;
    peak_drawdown_day: number;
    peak_drawdown_pct: number;
    total_milestones: number;
    steps: TimelineStep[];
  } | null>(null);

  const [activeStepIndex, setActiveStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // Fetch timeline simulation on mount or when shocks change
  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/stress/timeline`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            initial_shocks: initialShocks,
            portfolio_notional: portfolioNotional,
            time_horizon_days: HORIZONS,
          }),
        });
        if (res.ok) {
          const data = await res.json();
          setTimelineData(data);
        }
      } catch (e) {
        console.error("Timeline simulation failed", e);
      }
    };
    fetchTimeline();
  }, [initialShocks, portfolioNotional]);

  // Auto-play scrubber effect
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    if (isPlaying && timelineData?.steps) {
      timer = setInterval(() => {
        setActiveStepIndex((prev) => {
          if (prev >= timelineData.steps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1400);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlaying, timelineData]);

  const currentStep = timelineData?.steps[activeStepIndex];

  // Aggregate all milestones up to current step
  const accumulatedMilestones = timelineData?.steps
    .slice(0, activeStepIndex + 1)
    .flatMap((s) => s.milestones) || [];

  return (
    <div className="bg-[#0b101b] border border-slate-800 rounded-xl p-6 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              Dynamic Multi-Period Propagation Scrubber
            </h2>
            <p className="text-xs text-slate-400">
              PRD Section 16 • 0 to 90-Day Wave Contagion, Inventory Buffers &amp; Cascade Solvency
            </p>
          </div>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center space-x-2 bg-slate-900 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveStepIndex(0)}
            title="Reset to Day 0"
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            disabled={!timelineData}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-500 text-slate-950 font-bold text-xs hover:bg-cyan-400 transition"
          >
            {isPlaying ? (
              <>
                <Pause className="w-3.5 h-3.5 fill-slate-950" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-slate-950" />
                <span>Play Simulation</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Scrub Bar */}
      <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-xl space-y-4">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-slate-400 flex items-center space-x-1">
            <Calendar className="w-3.5 h-3.5 text-cyan-400" />
            <span>TIMELINE HORIZON</span>
          </span>
          <span className="text-cyan-400 font-bold text-sm">
            Day {currentStep?.day ?? 0} of 90
          </span>
        </div>

        {/* Step Buttons Bar */}
        <div className="grid grid-cols-7 gap-2">
          {HORIZONS.map((day, idx) => {
            const isSelected = activeStepIndex === idx;
            const isPast = activeStepIndex > idx;
            return (
              <button
                key={day}
                onClick={() => {
                  setActiveStepIndex(idx);
                  setIsPlaying(false);
                }}
                className={`py-2 px-1 rounded-lg text-xs font-mono transition flex flex-col items-center justify-center border ${
                  isSelected
                    ? "bg-cyan-500 text-slate-950 font-bold border-cyan-400 shadow-lg shadow-cyan-950/60"
                    : isPast
                    ? "bg-slate-900 text-cyan-400 border-cyan-900/40 hover:border-cyan-700"
                    : "bg-slate-950/60 text-slate-500 border-slate-800 hover:text-slate-300"
                }`}
              >
                <span className="text-[10px] uppercase">Horizon</span>
                <span className="text-sm font-bold">D+{day}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* State Display at Selected Day */}
      {currentStep && (
        <div className="space-y-6">
          {/* Key Indicators at Day t */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
              <div className="text-[11px] font-medium text-slate-400">Cumulative Drawdown</div>
              <div className="text-xl font-bold font-mono text-rose-400 mt-1">
                -${Math.abs(currentStep.cumulative_pnl).toLocaleString()}
              </div>
              <div className="text-[10px] font-mono text-rose-500">
                {currentStep.drawdown_pct.toFixed(1)}% of capital
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
              <div className="text-[11px] font-medium text-slate-400">Tail CVaR (99.0%)</div>
              <div className="text-xl font-bold font-mono text-amber-400 mt-1">
                ${currentStep.cvar_99.toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-500">Peak tail risk at current wave</div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
              <div className="text-[11px] font-medium text-slate-400">Infected Network Nodes</div>
              <div className="text-xl font-bold font-mono text-cyan-400 mt-1">
                {currentStep.active_nodes_count} Assets
              </div>
              <div className="text-[10px] text-slate-500">Direct &amp; multi-hop contagion</div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
              <div className="text-[11px] font-medium text-slate-400">Peak Historical Risk</div>
              <div className="text-xl font-bold font-mono text-rose-500 mt-1">
                Day {timelineData?.peak_drawdown_day}
              </div>
              <div className="text-[10px] text-slate-500">
                Max drawdown: {timelineData?.peak_drawdown_pct.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Inventory Depletion & Shock Gauges */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Inventory Buffer Depletion */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between text-xs font-bold text-slate-200">
                <span className="flex items-center space-x-1.5">
                  <Warehouse className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Remaining Safety Inventory Stock (Days)</span>
                </span>
                <span className="text-[10px] font-mono text-slate-400">τ_inv remaining</span>
              </div>
              <div className="space-y-2 text-xs font-mono">
                {Object.entries(currentStep.inventory_levels).slice(0, 5).map(([node, days]) => (
                  <div key={node} className="space-y-1">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-slate-300 font-bold">{node}</span>
                      <span className={days === 0 ? "text-rose-400 font-bold" : "text-cyan-400"}>
                        {days === 0 ? "EXHAUSTED (0d)" : `${days.toFixed(0)} days left`}
                      </span>
                    </div>
                    <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-slate-800">
                      <div
                        className={`h-full transition-all duration-300 ${
                          days === 0 ? "bg-rose-500" : "bg-cyan-500"
                        }`}
                        style={{ width: `${Math.min(100, (days / 45) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Asset Shock Magnitudes at Day t */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between text-xs font-bold text-slate-200">
                <span className="flex items-center space-x-1.5">
                  <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
                  <span>Propagated Shock Vector S_v(t)</span>
                </span>
                <span className="text-[10px] font-mono text-slate-400">Impact %</span>
              </div>
              <div className="space-y-2 text-xs font-mono">
                {Object.entries(currentStep.node_shocks)
                  .filter(([, shock]) => Math.abs(shock) > 0.01)
                  .slice(0, 5)
                  .map(([node, shock]) => (
                    <div key={node} className="flex justify-between items-center py-1 border-b border-slate-800/60">
                      <span className="text-slate-300 font-bold">{node}</span>
                      <span className="text-rose-400 font-bold font-mono">
                        {(shock * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          </div>

          {/* Chronological Milestone Feed */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
              <div className="text-xs font-bold text-slate-200 flex items-center space-x-2">
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                <span>Chronological Contagion Events (Day 0 to D+{currentStep.day})</span>
              </div>
              <span className="text-[10px] font-mono text-slate-400">
                {accumulatedMilestones.length} Events Triggered
              </span>
            </div>
            <div className="p-4 space-y-2.5 max-h-56 overflow-y-auto">
              {accumulatedMilestones.map((m, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border text-xs flex items-start space-x-3 transition ${
                    m.severity === "CRITICAL"
                      ? "bg-rose-950/20 border-rose-800/60 text-rose-200"
                      : m.severity === "WARNING"
                      ? "bg-amber-950/20 border-amber-800/60 text-amber-200"
                      : "bg-cyan-950/20 border-cyan-800/60 text-cyan-200"
                  }`}
                >
                  <div className="mt-0.5">
                    {m.severity === "CRITICAL" ? (
                      <AlertOctagon className="w-4 h-4 text-rose-400" />
                    ) : m.severity === "WARNING" ? (
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                    ) : (
                      <Info className="w-4 h-4 text-cyan-400" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-[11px] px-1.5 py-0.5 rounded bg-black/40">
                        Day {m.day}
                      </span>
                      <span className="font-bold text-xs">{m.node_id}</span>
                      <span className="text-[10px] uppercase font-mono opacity-70">
                        [{m.event_type}]
                      </span>
                    </div>
                    <div className="text-[11px] mt-1 opacity-90">{m.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
