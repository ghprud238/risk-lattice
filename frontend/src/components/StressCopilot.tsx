"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Send,
  Bot,
  User,
  CheckCircle2,
  ArrowRight,
  RefreshCw,
} from "lucide-react";

interface CopilotAnswer {
  query: string;
  intent: string;
  headline: string;
  detailed_analysis: string;
  key_metrics: Record<string, any>;
  verbatim_citations: Array<{ entity: string; quote: string }>;
  recommended_actions: string[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5051";

export default function StressCopilot() {
  const [messages, setMessages] = useState<
    Array<{ role: "user" | "copilot"; text?: string; data?: CopilotAnswer }>
  >([
    {
      role: "copilot",
      text: "Hello, Chief Risk Officer. I am RiskLattice Copilot. You can ask me about multi-tier supply chain bottlenecks, portfolio tail-risk exposures, inventory buffer depletion, or capital-efficient hedge recommendations.",
    },
  ]);
  const [inputQuery, setInputQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const PRESET_QUERIES = [
    "What is our exposure to TSMC Fab 18 in Taiwan?",
    "Which portfolio holding has the lowest inventory buffer?",
    "Recommend an optimal $500k tail hedge basket.",
    "How does a 40% oil spike affect our industrials book?",
  ];

  const handleSend = async (queryText: string) => {
    if (!queryText.trim()) return;
    const userQ = queryText.trim();
    setInputQuery("");
    setMessages((prev) => [...prev, { role: "user", text: userQ }]);
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/copilot/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userQ }),
      });
      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [...prev, { role: "copilot", data }]);
      }
    } catch (e) {
      console.error("Copilot request failed", e);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-[#0b101b] border border-slate-800 rounded-xl p-6 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-purple-950/60 border border-purple-800/60 flex items-center justify-center text-purple-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              AI Conversational Stress Copilot
            </h2>
            <p className="text-xs text-slate-400">
              PRD Section 16 • Deterministic Graph Querying, SEC 10-K Verbatim Citations &amp; Mitigation Actions
            </p>
          </div>
        </div>
      </div>

      {/* Preset Query Pills */}
      <div className="flex flex-wrap gap-2 text-xs">
        {PRESET_QUERIES.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition text-[11px] font-mono flex items-center space-x-1.5"
          >
            <span>{q}</span>
            <ArrowRight className="w-3 h-3 text-cyan-400" />
          </button>
        ))}
      </div>

      {/* Chat Messages Log */}
      <div className="space-y-4 max-h-[500px] overflow-y-auto p-4 bg-slate-950/70 border border-slate-800/90 rounded-xl">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex items-start space-x-3 text-xs ${
              m.role === "user" ? "flex-row-reverse space-x-reverse" : ""
            }`}
          >
            <div
              className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                m.role === "user"
                  ? "bg-cyan-600 text-white"
                  : "bg-purple-950 border border-purple-800 text-purple-400"
              }`}
            >
              {m.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`p-4 rounded-xl max-w-2xl space-y-3 ${
                m.role === "user"
                  ? "bg-cyan-950/40 border border-cyan-800 text-slate-200"
                  : "bg-slate-900/90 border border-slate-800 text-slate-300"
              }`}
            >
              {m.text && <p className="leading-relaxed">{m.text}</p>}

              {/* Structured Copilot Answer Card */}
              {m.data && (
                <div className="space-y-4">
                  <div className="border-b border-slate-800 pb-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-950 text-purple-400 border border-purple-800">
                      {m.data.intent}
                    </span>
                    <h4 className="text-sm font-bold text-white mt-1.5">{m.data.headline}</h4>
                  </div>

                  <p className="leading-relaxed text-slate-300">{m.data.detailed_analysis}</p>

                  {/* Key Metrics Grid */}
                  {Object.keys(m.data.key_metrics || {}).length > 0 && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono">
                      {Object.entries(m.data.key_metrics).map(([k, v]) => (
                        <div key={k} className="p-2 rounded bg-slate-950 border border-slate-800">
                          <div className="text-[9px] text-slate-500 uppercase">{k.replace(/_/g, " ")}</div>
                          <div className="text-xs font-bold text-cyan-400 mt-0.5">{String(v)}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* SEC 10-K Verbatim Quotes */}
                  {m.data.verbatim_citations?.length > 0 && (
                    <div className="p-3 rounded-lg bg-slate-950/90 border border-slate-800/80 space-y-1">
                      <div className="text-[10px] font-bold text-cyan-400 uppercase font-mono">
                        Audited SEC 10-K Ground Truth
                      </div>
                      {m.data.verbatim_citations.map((c, i) => (
                        <div key={i} className="text-[11px] text-slate-400 italic">
                          &ldquo;{c.quote}&rdquo; &mdash; <strong className="text-slate-300">{c.entity}</strong>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Action Recommendations */}
                  {m.data.recommended_actions?.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      <div className="text-[10px] font-bold text-slate-400 uppercase font-mono">
                        Recommended Mitigations
                      </div>
                      {m.data.recommended_actions.map((act, i) => (
                        <div
                          key={i}
                          className="flex items-center space-x-2 text-[11px] text-emerald-400"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                          <span>{act}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend(inputQuery);
        }}
        className="flex items-center space-x-2 bg-slate-950 p-2 rounded-xl border border-slate-800"
      >
        <input
          type="text"
          placeholder="Ask Risk Copilot (e.g. 'What is our exposure to TSMC Fab 18 in Taiwan?')..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          disabled={isLoading}
          className="flex-1 bg-transparent px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={isLoading || !inputQuery.trim()}
          className="px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white font-bold text-xs rounded-lg flex items-center space-x-1.5 transition disabled:opacity-50"
        >
          {isLoading ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Send className="w-3.5 h-3.5" />
          )}
          <span>{isLoading ? "Querying..." : "Send"}</span>
        </button>
      </form>
    </div>
  );
}
