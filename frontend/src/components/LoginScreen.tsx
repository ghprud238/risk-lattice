"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  ShieldAlert,
  Network,
  Lock,
  ArrowRight,
  CheckCircle2,
  Building2,
  UserCheck,
  Cpu,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { useAuth, UserRole } from "@/context/AuthContext";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

export default function LoginScreen() {
  const { loginWithGoogleCredential, loginWithPersona, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<"google" | "personas">("google");
  const [customEmail, setCustomEmail] = useState("");
  const [customName, setCustomName] = useState("");
  const [customOrg, setCustomOrg] = useState("");
  const [customRole, setCustomRole] = useState<UserRole>("CHIEF_RISK_OFFICER");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const googleBtnRef = useRef<HTMLDivElement>(null);

  // Initialize Google Identity Services (GIS) if Client ID is configured
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      if ((window as any).google?.accounts?.id) {
        (window as any).google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: (response: any) => {
            if (response.credential) {
              loginWithGoogleCredential(response.credential).catch(() => {
                setErrorMsg("Google authentication failed. Please try again.");
              });
            }
          },
        });

        if (googleBtnRef.current) {
          (window as any).google.accounts.id.renderButton(googleBtnRef.current, {
            theme: "filled_blue",
            size: "large",
            shape: "pill",
            width: 320,
            text: "continue_with",
          });
        }
      }
    };
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, [loginWithGoogleCredential]);

  const handleSimulatedGoogleLogin = async () => {
    setErrorMsg(null);
    // Instant Google Workspace OAuth emulation
    const success = await loginWithPersona(
      "alex.turner@institutional-risk.google.com",
      "Alex Turner",
      "CHIEF_RISK_OFFICER",
      "Google Cloud Financial Services"
    );
    if (!success) {
      setErrorMsg("Failed to authenticate session.");
    }
  };

  const handlePersonaSelect = async (
    email: string,
    name: string,
    role: UserRole,
    org: string
  ) => {
    setErrorMsg(null);
    const success = await loginWithPersona(email, name, role, org);
    if (!success) {
      setErrorMsg("Failed to authenticate persona.");
    }
  };

  const handleCustomSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customEmail) {
      setErrorMsg("Please provide an institutional email address.");
      return;
    }
    setErrorMsg(null);
    const success = await loginWithPersona(
      customEmail,
      customName || customEmail.split("@")[0],
      customRole,
      customOrg || "Institutional Asset Management"
    );
    if (!success) {
      setErrorMsg("Failed to authenticate custom persona.");
    }
  };

  return (
    <div className="min-h-screen bg-[#070b12] text-slate-100 flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Background Matrix / Grid Effects */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0d1527_1px,transparent_1px),linear-gradient(to_bottom,#0d1527_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_40%,#000_70%,transparent_100%)] opacity-40 pointer-events-none" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-cyan-500/10 blur-[130px] rounded-full pointer-events-none" />

      {/* Main Authentication Card */}
      <div className="w-full max-w-md z-10 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-gradient-to-br from-cyan-500 via-blue-600 to-indigo-700 text-slate-950 shadow-xl shadow-cyan-500/20 mb-2">
            <Network className="w-7 h-7 stroke-[2.5]" />
          </div>
          <div className="flex items-center justify-center space-x-2">
            <h1 className="text-2xl font-black tracking-tight text-white">
              Risk<span className="text-cyan-400">Lattice</span>
            </h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
              ENTERPRISE SSO
            </span>
          </div>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Cross-Asset Macro Contagion Stress-Tester • 4-Hop Damped Network Propagation &amp; Copula CVaR
          </p>
        </div>

        {/* Card Body */}
        <div className="bg-[#0b101b]/90 border border-slate-800/90 rounded-2xl p-6 shadow-2xl backdrop-blur-xl space-y-5">
          {errorMsg && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Tab Selector */}
          <div className="flex rounded-xl bg-slate-900/90 p-1 border border-slate-800 text-xs font-medium">
            <button
              onClick={() => setActiveTab("google")}
              className={`flex-1 py-2 rounded-lg transition flex items-center justify-center space-x-2 ${
                activeTab === "google"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <span>Google Login</span>
            </button>
            <button
              onClick={() => setActiveTab("personas")}
              className={`flex-1 py-2 rounded-lg transition flex items-center justify-center space-x-2 ${
                activeTab === "personas"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <span>Sandbox Personas</span>
            </button>
          </div>

          {activeTab === "google" && (
            <div className="space-y-4">
              <p className="text-xs text-slate-400 text-center">
                Sign in with your verified institutional Google Workspace account or enterprise OAuth identity.
              </p>

              {/* Native Google One-Tap Container (if Client ID present) */}
              {GOOGLE_CLIENT_ID && (
                <div className="flex justify-center my-3" ref={googleBtnRef}></div>
              )}

              {/* Primary Google Login Button */}
              <button
                onClick={handleSimulatedGoogleLogin}
                disabled={isLoading}
                className="w-full py-3 px-4 rounded-xl bg-white hover:bg-slate-100 text-slate-900 font-semibold text-xs transition duration-200 shadow-lg shadow-white/5 flex items-center justify-center space-x-3 border border-slate-200 active:scale-[0.98] disabled:opacity-50"
              >
                {/* Official Google 'G' SVG Logo */}
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
                <span>Continue with Google Workspace</span>
              </button>

              <div className="pt-2 text-[11px] text-slate-500 text-center flex items-center justify-center space-x-1">
                <Lock className="w-3 h-3 text-slate-500" />
                <span>Protected by Fed SR 11-7 Model Governance &amp; Rule P-01</span>
              </div>
            </div>
          )}

          {activeTab === "personas" && (
            <div className="space-y-4">
              <p className="text-[11px] text-slate-400">
                Select an institutional persona for evaluation and stress testing:
              </p>

              {/* Persona Cards */}
              <div className="space-y-2">
                <button
                  onClick={() =>
                    handlePersonaSelect(
                      "sarah.chen@citadel-macro.com",
                      "Sarah Chen",
                      "CHIEF_RISK_OFFICER",
                      "Citadel Macro Fund"
                    )
                  }
                  className="w-full text-left p-3 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800/80 hover:border-cyan-500/50 transition duration-150 group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2.5">
                      <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-xs">
                        SC
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white group-hover:text-cyan-400 transition">
                          Sarah Chen
                        </div>
                        <div className="text-[10px] text-slate-400">
                          Chief Risk Officer • Citadel Macro Fund
                        </div>
                      </div>
                    </div>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-cyan-950 text-cyan-400 border border-cyan-800">
                      CRO
                    </span>
                  </div>
                </button>

                <button
                  onClick={() =>
                    handlePersonaSelect(
                      "marcus.vance@point72-tmt.com",
                      "Marcus Vance",
                      "PORTFOLIO_MANAGER",
                      "Point72 Asset Management"
                    )
                  }
                  className="w-full text-left p-3 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800/80 hover:border-cyan-500/50 transition duration-150 group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2.5">
                      <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-xs">
                        MV
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white group-hover:text-cyan-400 transition">
                          Marcus Vance
                        </div>
                        <div className="text-[10px] text-slate-400">
                          Quant Portfolio Manager • Point72 TMT Pod
                        </div>
                      </div>
                    </div>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-blue-950 text-blue-400 border border-blue-800">
                      PM
                    </span>
                  </div>
                </button>

                <button
                  onClick={() =>
                    handlePersonaSelect(
                      "elena.rostova@jpmorgan-risk.com",
                      "Elena Rostova",
                      "ANALYST",
                      "JPMorgan Chase & Co."
                    )
                  }
                  className="w-full text-left p-3 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800/80 hover:border-cyan-500/50 transition duration-150 group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2.5">
                      <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs">
                        ER
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white group-hover:text-cyan-400 transition">
                          Elena Rostova
                        </div>
                        <div className="text-[10px] text-slate-400">
                          Senior Risk Analyst • JPMorgan CCAR Desk
                        </div>
                      </div>
                    </div>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                      ANALYST
                    </span>
                  </div>
                </button>
              </div>

              {/* Custom Write-In Form */}
              <form onSubmit={handleCustomSubmit} className="pt-3 border-t border-slate-800/80 space-y-2.5">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Or Custom Institutional Email
                </div>
                <input
                  type="email"
                  placeholder="name@fund-name.com"
                  value={customEmail}
                  onChange={(e) => setCustomEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500"
                />
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-2 px-3 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition flex items-center justify-center space-x-1.5 shadow"
                >
                  <span>Enter Command Center</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </form>
            </div>
          )}
        </div>

        {/* Security & Regulatory Highlights */}
        <div className="grid grid-cols-3 gap-2 text-center text-[10px] text-slate-500">
          <div className="p-2 rounded-xl bg-slate-950/40 border border-slate-900">
            <span className="block font-bold text-slate-400">Fed SR 11-7</span>
            <span>Model Governed</span>
          </div>
          <div className="p-2 rounded-xl bg-slate-950/40 border border-slate-900">
            <span className="block font-bold text-slate-400">Rule P-01</span>
            <span>Zero Data Egress</span>
          </div>
          <div className="p-2 rounded-xl bg-slate-950/40 border border-slate-900">
            <span className="block font-bold text-slate-400">AST Isolated</span>
            <span>Pure C/Python Math</span>
          </div>
        </div>
      </div>
    </div>
  );
}
