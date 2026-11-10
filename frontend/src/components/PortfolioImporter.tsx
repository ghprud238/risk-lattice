"use client";

import React, { useState } from "react";
import { UploadCloud, Shield, FileText, CheckCircle2, AlertTriangle, FileCode } from "lucide-react";

interface PortfolioImporterProps {
  onIngestPortfolio: (holdings: Record<string, number>) => Promise<void>;
  onExtractFiling: (chunkText: string, ticker: string) => Promise<any>;
}

const DEFAULT_HOLDINGS: Record<string, number> = {
  NVDA: 0.20,
  TSLA: 0.20,
  BA: 0.15,
  DAL: 0.15,
  F: 0.15,
  KRE: 0.15
};

const SAMPLE_FILING_TEXT = `We rely on a single foundry for the manufacturing of all our advanced Blackwell and Hopper GPUs. Substantially all of our wafer manufacturing is performed by Taiwan Semiconductor Manufacturing Company (TSMC) at its facilities in Hsinchu and Tainan, Taiwan. Approximately 68% of our neural-engine wafers are fabricated by a single foundry in Hsinchu, Taiwan. If TSMC experiences manufacturing disruptions, earthquakes, or regional geopolitical conflict, our product shipments would be substantially halted.`;

export default function PortfolioImporter({
  onIngestPortfolio,
  onExtractFiling
}: PortfolioImporterProps) {
  const [holdings, setHoldings] = useState<Record<string, number>>(DEFAULT_HOLDINGS);
  const [rawPiiText, setRawPiiText] = useState(
    "Private Ledger Acct #8841-SECURE: 50,000 shares of NVDA ($6,500,000), 30,000 shares of TSLA ($7,200,000), and $1,500,000 cash balance."
  );
  const [sanitizedPreview, setSanitizedPreview] = useState<string>("");

  const [filingTicker, setFilingTicker] = useState("NVDA");
  const [filingText, setFilingText] = useState(SAMPLE_FILING_TEXT);
  const [extractionResult, setExtractionResult] = useState<any>(null);
  const [isExtracting, setIsExtracting] = useState(false);

  const handleWeightChange = (ticker: string, val: number) => {
    setHoldings((prev) => ({ ...prev, [ticker]: val }));
  };

  const handleApplyHoldings = () => {
    onIngestPortfolio(holdings);
  };

  const handleSimulateSanitizer = () => {
    // Redact dollars, shares, accounts
    let text = rawPiiText;
    text = text.replace(/#[\w\-]{6,}/g, "[REDACTED_ACCOUNT]");
    text = text.replace(/\$[\d,]+(\.\d+)?/g, "[REDACTED_AMOUNT]");
    text = text.replace(/\b\d+([,\d]*)\s*(shares|units)\b/gi, "[REDACTED_QUANTITY]");
    setSanitizedPreview(text);
  };

  const handleRunExtract = async () => {
    setIsExtracting(true);
    try {
      const res = await onExtractFiling(filingText, filingTicker);
      setExtractionResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {/* Portfolio Importer & Privacy Sanitizer */}
      <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-5 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
          <Shield className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
            Portfolio Importer & Local Privacy Boundary
          </h3>
        </div>

        <p className="text-xs text-slate-400">
          Strict Architectural Guardrail: Portfolio dollar balances and share quantities remain inside DuckDB.
          Tier 3 LLM receives ONLY tickers and normalized percentages.
        </p>

        {/* Weights Matrix */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300">Active Portfolio Allocations</label>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(holdings).map(([ticker, weight]) => (
              <div key={ticker} className="bg-slate-950 p-2 rounded border border-slate-800 text-xs">
                <span className="font-bold text-cyan-400 font-mono">{ticker}</span>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={weight}
                  onChange={(e) => handleWeightChange(ticker, parseFloat(e.target.value) || 0)}
                  className="w-full mt-1 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 font-mono text-xs focus:outline-none"
                />
              </div>
            ))}
          </div>

          <button
            onClick={handleApplyHoldings}
            className="w-full mt-2 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition"
          >
            Apply & Normalize Portfolio
          </button>
        </div>

        {/* Client-Side PII Sanitizer Demo */}
        <div className="pt-3 border-t border-slate-800 space-y-2">
          <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
            <span>Client-Side PII & Position Sanitizer Sandbox</span>
            <button
              onClick={handleSimulateSanitizer}
              className="text-[11px] text-cyan-400 hover:underline"
            >
              Test Sanitizer
            </button>
          </label>
          <textarea
            rows={2}
            value={rawPiiText}
            onChange={(e) => setRawPiiText(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-xs font-mono text-slate-300 focus:outline-none"
          />
          {sanitizedPreview && (
            <div className="bg-slate-950/80 p-2.5 rounded border border-cyan-900/60 text-xs font-mono text-cyan-300">
              <span className="text-[10px] text-slate-500 block">Sanitized Prompt Payload (Sent to Tier 3):</span>
              {sanitizedPreview}
            </div>
          )}
        </div>
      </div>

      {/* SEC 10-K Graph Extractor Sandbox */}
      <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-5 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
          <FileText className="w-5 h-5 text-amber-400" />
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
            SEC 10-K Entity Extractor Sandbox
          </h3>
        </div>

        <p className="text-xs text-slate-400">
          Strict Anti-Hallucination Gate: Edges are validated against Pydantic schema and rejected if the evidence quote is not found verbatim in the source text.
        </p>

        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-300">Company Ticker:</span>
            <input
              type="text"
              value={filingTicker}
              onChange={(e) => setFilingTicker(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-xs text-slate-200 font-mono"
            />
          </div>

          <textarea
            rows={5}
            value={filingText}
            onChange={(e) => setFilingText(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-200 font-mono focus:outline-none"
          />

          <button
            onClick={handleRunExtract}
            disabled={isExtracting}
            className="w-full py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition disabled:opacity-50"
          >
            {isExtracting ? "Extracting & Verifying Quotes..." : "Extract Typed Graph Edges"}
          </button>
        </div>

        {/* Extraction Results */}
        {extractionResult && (
          <div className="pt-2 border-t border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-200">
                Extracted Edges ({extractionResult.extracted_edges_count}):
              </span>
              <span className="inline-flex items-center space-x-1 text-emerald-400 text-[11px] font-bold">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>VERBATIM QUOTE VERIFIED</span>
              </span>
            </div>

            <div className="space-y-1.5 max-h-40 overflow-y-auto">
              {extractionResult.edges?.map((e: any, idx: number) => (
                <div key={idx} className="bg-slate-950 p-2.5 rounded border border-slate-800 text-[11px] font-mono">
                  <div className="flex items-center space-x-2 text-cyan-300 font-bold">
                    <span>{e.source_id}</span>
                    <span className="text-slate-500">→</span>
                    <span>{e.target_id}</span>
                    <span className="px-1.5 py-0.2 rounded bg-slate-800 text-[10px] text-amber-300">
                      {e.relation_type}
                    </span>
                    <span className="text-slate-400 text-[10px]">
                      (Weight: {e.base_weight}, Lag: {e.lag_days}d)
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1 italic">
                    &ldquo;{e.evidence_quote}&rdquo;
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
