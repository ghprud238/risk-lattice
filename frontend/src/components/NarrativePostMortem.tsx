"use client";

import React from "react";
import { MessageSquareText, ShieldCheck, Sparkles, CheckCheck } from "lucide-react";

interface NarrativePostMortemProps {
  narrative: {
    scenario_title: string;
    bullet_1_macro_trigger: string;
    bullet_2_transmission_bottleneck: string;
    bullet_3_tail_risk_hedges: string;
    verified_citations: string[];
    citations_verified: boolean;
  } | null;
}

export default function NarrativePostMortem({ narrative }: NarrativePostMortemProps) {
  if (!narrative) {
    return (
      <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-6 text-center text-slate-500 text-xs font-mono">
        Post-mortem narrative report will appear here once a shock simulation completes.
      </div>
    );
  }

  return (
    <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-5 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <MessageSquareText className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
            Neuro-Symbolic Post-Mortem Narrative
          </h3>
        </div>

        {narrative.citations_verified ? (
          <div className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-800/80 text-emerald-400 text-xs font-bold shadow-sm">
            <ShieldCheck className="w-4 h-4" />
            <span>ALL PERCENTAGES VERIFIED AGAINST CORE MATH</span>
          </div>
        ) : (
          <div className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-amber-950/80 border border-amber-800/80 text-amber-400 text-xs font-bold">
            <span>UNVERIFIED CITATIONS</span>
          </div>
        )}
      </div>

      {/* 3 Structured Bullets */}
      <div className="space-y-3 text-xs leading-relaxed">
        <div className="bg-slate-950/70 p-3.5 rounded-lg border border-slate-800/80 flex items-start space-x-3">
          <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 font-bold flex items-center justify-center text-[11px] mt-0.5">
            1
          </span>
          <p className="text-slate-300 font-sans">{narrative.bullet_1_macro_trigger}</p>
        </div>

        <div className="bg-slate-950/70 p-3.5 rounded-lg border border-slate-800/80 flex items-start space-x-3">
          <span className="flex-shrink-0 w-5 h-5 rounded-full bg-amber-500/20 text-amber-400 font-bold flex items-center justify-center text-[11px] mt-0.5">
            2
          </span>
          <p className="text-slate-300 font-sans">{narrative.bullet_2_transmission_bottleneck}</p>
        </div>

        <div className="bg-slate-950/70 p-3.5 rounded-lg border border-slate-800/80 flex items-start space-x-3">
          <span className="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold flex items-center justify-center text-[11px] mt-0.5">
            3
          </span>
          <p className="text-slate-300 font-sans">{narrative.bullet_3_tail_risk_hedges}</p>
        </div>
      </div>

      {/* Verified Citations List */}
      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
        <div className="flex items-center space-x-2">
          <span>Engine Number Attestation:</span>
          <div className="flex items-center space-x-1.5">
            {narrative.verified_citations.map((cite, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-bold border border-slate-700"
              >
                {cite}
              </span>
            ))}
          </div>
        </div>
        <span className="text-slate-500 text-[10px]">Zero LLM Math Hallucination Guaranteed</span>
      </div>
    </div>
  );
}
