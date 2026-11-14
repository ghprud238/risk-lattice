"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Lock,
  CheckCircle2,
  AlertTriangle,
  X,
  FileCheck,
  KeyRound,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

interface AuditEntry {
  entry_id: string;
  run_id: string;
  scenario_name: string;
  status: "DRAFT" | "PENDING_REVIEW" | "APPROVED_BY_CRO" | "REJECTED" | "LOCKED_REGULATORY";
  submitted_by: string;
  submitted_by_role: string;
  submitted_at: string;
  pnl_impact: number;
  cvar_99: number;
  shock_summary: Record<string, number>;
  approved_by?: string;
  approved_by_role?: string;
  approved_at?: string;
  comments?: string;
  cryptographic_seal_sha256?: string;
}

interface RegulatorySignoffModalProps {
  isOpen: boolean;
  onClose: () => void;
  runId?: string;
  scenarioName?: string;
  pnlImpact?: number;
  cvar99?: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5051";

export default function RegulatorySignoffModal({
  isOpen,
  onClose,
  runId = "run-citadel-202611-001",
  scenarioName = "Taiwan Foundry Disruption - High Severity",
  pnlImpact = -23450000,
  cvar99 = 29312500,
}: RegulatorySignoffModalProps) {
  const { user } = useAuth();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [croNotes, setCroNotes] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchEntries = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/audit/entries`);
      if (res.ok) {
        const data = await res.json();
        setEntries(data.entries || []);
      }
    } catch (e) {
      console.error("Failed to load audit entries", e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchEntries();
      setErrorMessage(null);
      setSuccessMessage(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Active run from vault or default
  const activeEntry = entries.find((e) => e.run_id === runId) || entries[0];
  const isSubmitter = user?.email?.toLowerCase() === activeEntry?.submitted_by?.toLowerCase();
  const isCRO = user?.role === "CHIEF_RISK_OFFICER";
  const isAuditor = user?.role === "AUDITOR";

  // Step 1: Submit for review
  const handleSubmitReview = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/audit/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          run_id: runId,
          scenario_name: scenarioName,
          submitted_by: user?.email || "analyst@citadel.com",
          submitted_by_role: user?.role || "PORTFOLIO_MANAGER",
          pnl_impact: pnlImpact,
          cvar_99: cvar99,
          shock_summary: { FOUNDRY_TW: -0.40, BALTIC_DRY: -0.25 },
          comments: "Submitted for monthly stress governance review.",
        }),
      });
      if (res.ok) {
        setSuccessMessage("Run successfully submitted for CRO review.");
        await fetchEntries();
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || "Submission failed");
      }
    } catch (e: any) {
      setErrorMessage(e.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Step 2: CRO Sign-off
  const handleApprove = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/audit/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          run_id: runId,
          approver_email: user?.email || "sarah.chen@citadel.com",
          approver_role: user?.role || "CHIEF_RISK_OFFICER",
          comments: croNotes || "Approved after inspecting inventory buffers.",
        }),
      });
      if (res.ok) {
        setSuccessMessage("Approved! Cryptographic SHA-256 seal generated.");
        await fetchEntries();
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || "Approval rejected");
      }
    } catch (e: any) {
      setErrorMessage(e.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Step 3: Lock for Regulators
  const handleLock = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/audit/lock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          run_id: runId,
          auditor_email: user?.email || "compliance@citadel.com",
        }),
      });
      if (res.ok) {
        setSuccessMessage("Run permanently locked into SR 11-7 Regulatory Packet.");
        await fetchEntries();
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || "Locking failed");
      }
    } catch (e: any) {
      setErrorMessage(e.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="bg-[#0b101b] border border-slate-700 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-800/80 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white tracking-wide">
                Four-Eyes Governance Sign-off &amp; Audit Vault
              </h3>
              <p className="text-[11px] text-slate-400">
                FRTB / BCBS 239 / Fed SR 11-7 Cryptographic Tamper-Evident Sign-off
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Active Persona Banner */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2.5">
              <KeyRound className="w-4 h-4 text-cyan-400" />
              <div>
                <span className="text-slate-400">Active Identity: </span>
                <strong className="text-white">{user?.name}</strong>
                <span className="text-slate-500 font-mono text-[10px] ml-1.5">
                  ({user?.email})
                </span>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950 text-cyan-400 border border-cyan-800/60">
              {user?.role}
            </span>
          </div>

          {/* Alert Messages */}
          {errorMessage && (
            <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 text-xs flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Active Run Governance Card */}
          {activeEntry && (
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-white">{activeEntry.scenario_name}</div>
                  <div className="text-[10px] font-mono text-slate-500">Run ID: {activeEntry.run_id}</div>
                </div>
                <span
                  className={`px-2.5 py-1 rounded text-[11px] font-mono font-bold ${
                    activeEntry.status === "APPROVED_BY_CRO"
                      ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                      : activeEntry.status === "LOCKED_REGULATORY"
                      ? "bg-purple-950 text-purple-400 border border-purple-800"
                      : "bg-amber-950 text-amber-400 border border-amber-800"
                  }`}
                >
                  {activeEntry.status}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80">
                  <div className="text-[10px] text-slate-500 uppercase">PnL Impact</div>
                  <div className="text-rose-400 font-bold mt-0.5">
                    -${Math.abs(activeEntry.pnl_impact).toLocaleString()}
                  </div>
                </div>
                <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80">
                  <div className="text-[10px] text-slate-500 uppercase">CVaR (99%)</div>
                  <div className="text-amber-400 font-bold mt-0.5">
                    ${activeEntry.cvar_99.toLocaleString()}
                  </div>
                </div>
                <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80">
                  <div className="text-[10px] text-slate-500 uppercase">Submitted By</div>
                  <div className="text-slate-300 truncate mt-0.5" title={activeEntry.submitted_by}>
                    {activeEntry.submitted_by.split("@")[0]}
                  </div>
                </div>
                <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80">
                  <div className="text-[10px] text-slate-500 uppercase">Approver</div>
                  <div className="text-emerald-400 font-bold truncate mt-0.5">
                    {activeEntry.approved_by ? activeEntry.approved_by.split("@")[0] : "Pending..."}
                  </div>
                </div>
              </div>

              {/* Cryptographic Seal */}
              {activeEntry.cryptographic_seal_sha256 && (
                <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-800/60 space-y-1">
                  <div className="flex items-center space-x-1.5 text-xs font-bold text-emerald-400">
                    <FileCheck className="w-3.5 h-3.5" />
                    <span>Cryptographic Audit Seal (SHA-256)</span>
                  </div>
                  <div className="font-mono text-[11px] text-emerald-300 break-all select-all">
                    {activeEntry.cryptographic_seal_sha256}
                  </div>
                </div>
              )}

              {/* Four-Eyes Sign-off Controls */}
              <div className="pt-2 border-t border-slate-800 space-y-3">
                {activeEntry.status === "DRAFT" && (
                  <button
                    onClick={handleSubmitReview}
                    disabled={isSubmitting}
                    className="w-full py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs shadow transition disabled:opacity-50"
                  >
                    Submit for Independent CRO Review
                  </button>
                )}

                {isSubmitter && activeEntry.status === "PENDING_REVIEW" && (
                  <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-800 text-amber-300 text-xs flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    <span>
                      <strong>Four-Eyes Enforcement:</strong> You submitted this run. An independent Chief Risk Officer must inspect and sign off.
                    </span>
                  </div>
                )}

                {isCRO && activeEntry.status === "PENDING_REVIEW" && !isSubmitter && (
                  <div className="space-y-3">
                    <textarea
                      placeholder="Add Chief Risk Officer review notes (e.g. verified inventory buffer, required put options)..."
                      value={croNotes}
                      onChange={(e) => setCroNotes(e.target.value)}
                      className="w-full h-20 p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                    />
                    <button
                      onClick={handleApprove}
                      disabled={isSubmitting}
                      className="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-slate-950 font-bold text-xs shadow flex items-center justify-center space-x-2 transition disabled:opacity-50"
                    >
                      <ShieldCheck className="w-4 h-4 fill-slate-950" />
                      <span>Approve Scenario Run &amp; Generate SHA-256 Seal</span>
                    </button>
                  </div>
                )}

                {(isAuditor || isCRO) && activeEntry.status === "APPROVED_BY_CRO" && (
                  <button
                    onClick={handleLock}
                    disabled={isSubmitting}
                    className="w-full py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow flex items-center justify-center space-x-2 transition disabled:opacity-50"
                  >
                    <Lock className="w-4 h-4" />
                    <span>Lock into Regulatory Audit Vault (SR 11-7 Compliant)</span>
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Historical Vault Log */}
          <div className="space-y-3">
            <div className="text-xs font-bold text-slate-300">
              Audit Vault Log ({entries.length} Historic Runs)
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {entries.map((ent) => (
                <div
                  key={ent.run_id}
                  className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs flex items-center justify-between"
                >
                  <div>
                    <div className="font-semibold text-white">{ent.scenario_name}</div>
                    <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                      {ent.run_id} • By: {ent.submitted_by.split("@")[0]} ({ent.submitted_by_role})
                    </div>
                  </div>
                  <div className="text-right">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        ent.status === "APPROVED_BY_CRO"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : ent.status === "LOCKED_REGULATORY"
                          ? "bg-purple-950 text-purple-400 border border-purple-800"
                          : "bg-amber-950 text-amber-400 border border-amber-800"
                      }`}
                    >
                      {ent.status}
                    </span>
                    <div className="text-[10px] font-mono text-slate-500 mt-1">
                      {ent.cryptographic_seal_sha256 ? "SEALED" : "UNSEALED"}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
