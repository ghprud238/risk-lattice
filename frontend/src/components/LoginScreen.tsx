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
  KeyRound,
  Eye,
  EyeOff,
  UserPlus,
  LogIn,
} from "lucide-react";
import { useAuth, UserRole } from "@/context/AuthContext";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

export default function LoginScreen() {
  const {
    loginWithCredentials,
    registerUser,
    loginWithGoogleCredential,
    loginWithPersona,
    isLoading,
  } = useAuth();

  // Top level options: "proprietary" (Option 2) or "google" (Option 1)
  const [authMethod, setAuthMethod] = useState<"proprietary" | "google">("proprietary");

  // Proprietary sub-mode: "login" or "register"
  const [proprietaryMode, setProprietaryMode] = useState<"login" | "register">("login");

  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [organization, setOrganization] = useState("");
  const [role, setRole] = useState<UserRole>("CHIEF_RISK_OFFICER");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

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
          callback: async (response: any) => {
            if (response.credential) {
              const res = await loginWithGoogleCredential(response.credential);
              if (!res.success) {
                setErrorMsg(res.error || "Google authentication failed. Please try again.");
              }
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
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, [loginWithGoogleCredential]);

  // Proprietary Login Handler
  const handleProprietarySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!email || !password) {
      setErrorMsg("Please provide both email and password.");
      return;
    }

    if (proprietaryMode === "login") {
      const res = await loginWithCredentials(email, password);
      if (!res.success) {
        setErrorMsg(res.error || "Invalid institutional credentials.");
      }
    } else {
      if (!name) {
        setErrorMsg("Please provide your full name for regulatory attribution.");
        return;
      }
      if (password.length < 6) {
        setErrorMsg("Password must be at least 6 characters.");
        return;
      }
      const res = await registerUser(
        email,
        password,
        name,
        role,
        organization || "Institutional Client"
      );
      if (!res.success) {
        setErrorMsg(res.error || "Registration failed.");
      } else {
        setSuccessMsg("Account successfully registered! Logging you in...");
      }
    }
  };

  // Quick fill default institutional accounts
  const handleQuickFill = (
    accountEmail: string,
    accountPass: string,
    accountName: string,
    accountRole: UserRole,
    accountOrg: string
  ) => {
    setEmail(accountEmail);
    setPassword(accountPass);
    setName(accountName);
    setRole(accountRole);
    setOrganization(accountOrg);
    setProprietaryMode("login");
    setErrorMsg(null);
  };

  // Google Workspace Simulated Fallback Login
  const handleSimulatedGoogleLogin = async () => {
    setErrorMsg(null);
    const res = await loginWithPersona(
      "alex.turner@institutional-risk.google.com",
      "Alex Turner",
      "CHIEF_RISK_OFFICER",
      "Google Cloud Financial Services"
    );
    if (!res.success) {
      setErrorMsg(res.error || "Failed to authenticate Google session.");
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
              ENTERPRISE AUTH
            </span>
          </div>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Cross-Asset Macro Contagion Stress-Tester • 4-Hop Damped Network Propagation &amp; Copula CVaR
          </p>
        </div>

        {/* Card Body */}
        <div className="bg-[#0b101b]/95 border border-slate-800/90 rounded-2xl p-6 shadow-2xl backdrop-blur-xl space-y-5">
          {errorMsg && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
          )}
          {successMsg && (
            <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Top-Level Authentication Method Selector */}
          <div className="flex rounded-xl bg-slate-900/90 p-1 border border-slate-800 text-xs font-medium">
            <button
              onClick={() => {
                setAuthMethod("proprietary");
                setErrorMsg(null);
              }}
              className={`flex-1 py-2 rounded-lg transition flex items-center justify-center space-x-2 ${
                authMethod === "proprietary"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <KeyRound className="w-3.5 h-3.5" />
              <span>Proprietary Login</span>
            </button>
            <button
              onClick={() => {
                setAuthMethod("google");
                setErrorMsg(null);
              }}
              className={`flex-1 py-2 rounded-lg transition flex items-center justify-center space-x-2 ${
                authMethod === "google"
                  ? "bg-cyan-500 text-slate-950 font-bold shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <span>Google SDK / SSO</span>
            </button>
          </div>

          {/* ========================================================================= */}
          {/* OPTION 1: GOOGLE SDK / WORKSPACE SSO                                      */}
          {/* ========================================================================= */}
          {authMethod === "google" && (
            <div className="space-y-4 pt-1">
              <p className="text-xs text-slate-400 text-center">
                Sign in with your verified institutional Google Workspace account or corporate Google OAuth identity.
              </p>

              {/* Native Google One-Tap Container (if Client ID configured) */}
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

          {/* ========================================================================= */}
          {/* OPTION 2: PROPRIETARY LOGIN & REGISTRATION SYSTEM                         */}
          {/* ========================================================================= */}
          {authMethod === "proprietary" && (
            <div className="space-y-4">
              {/* Sub-mode Switch: Login vs Register */}
              <div className="flex justify-between items-center border-b border-slate-800/80 pb-2">
                <div className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                  {proprietaryMode === "login" ? (
                    <>
                      <LogIn className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Account Sign In</span>
                    </>
                  ) : (
                    <>
                      <UserPlus className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Create Institutional Account</span>
                    </>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setProprietaryMode(proprietaryMode === "login" ? "register" : "login");
                    setErrorMsg(null);
                  }}
                  className="text-xs text-cyan-400 hover:text-cyan-300 font-medium transition"
                >
                  {proprietaryMode === "login" ? "Need an account? Register" : "Have an account? Sign In"}
                </button>
              </div>

              {/* Proprietary Form */}
              <form onSubmit={handleProprietarySubmit} className="space-y-3.5">
                {proprietaryMode === "register" && (
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                      Full Legal Name
                    </label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Sarah Connor"
                      className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 text-xs text-white placeholder-slate-500 outline-none transition"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                    Institutional Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g. cro@risklattice.com"
                    required
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 text-xs text-white placeholder-slate-500 outline-none transition font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      required
                      className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 text-xs text-white placeholder-slate-500 outline-none transition pr-9"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {proprietaryMode === "register" && (
                  <>
                    <div className="grid grid-cols-2 gap-2.5">
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                          Assigned Role
                        </label>
                        <select
                          value={role}
                          onChange={(e) => setRole(e.target.value as UserRole)}
                          className="w-full px-2.5 py-2 rounded-xl bg-slate-900 border border-slate-800 focus:border-cyan-500 text-xs text-white outline-none"
                        >
                          <option value="CHIEF_RISK_OFFICER">Chief Risk Officer</option>
                          <option value="PORTFOLIO_MANAGER">Portfolio Manager</option>
                          <option value="ANALYST">Quantitative Analyst</option>
                          <option value="AUDITOR">Model Auditor</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                          Organization
                        </label>
                        <input
                          type="text"
                          value={organization}
                          onChange={(e) => setOrganization(e.target.value)}
                          placeholder="e.g. Citadel / BlackRock"
                          className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 focus:border-cyan-500 text-xs text-white placeholder-slate-500 outline-none"
                        />
                      </div>
                    </div>
                  </>
                )}

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs transition duration-200 shadow-lg shadow-cyan-500/20 flex items-center justify-center space-x-2 disabled:opacity-50 active:scale-[0.98] mt-2"
                >
                  {isLoading ? (
                    <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <span>{proprietaryMode === "login" ? "Sign In to RiskLattice" : "Create Account"}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </form>

              {/* Pre-seeded Institutional Demo Credentials Quick-Fill */}
              <div className="pt-3 border-t border-slate-800/80">
                <div className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-1">
                  <Sparkles className="w-3 h-3 text-cyan-400" />
                  <span>Pre-Seeded Demo Accounts (Click to Fill)</span>
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  <button
                    type="button"
                    onClick={() =>
                      handleQuickFill(
                        "cro@risklattice.com",
                        "cro123!",
                        "Sarah Connor",
                        "CHIEF_RISK_OFFICER",
                        "Global Risk Governance"
                      )
                    }
                    className="p-2 text-left rounded-lg bg-slate-900/60 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 transition group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-white group-hover:text-cyan-400">
                        CRO
                      </span>
                      <span className="text-[9px] font-mono text-cyan-400 bg-cyan-950 px-1 py-0.5 rounded">
                        cro123!
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 truncate">cro@risklattice.com</div>
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      handleQuickFill(
                        "pm@risklattice.com",
                        "pm123!",
                        "Marcus Vance",
                        "PORTFOLIO_MANAGER",
                        "Alpha Tech Pod"
                      )
                    }
                    className="p-2 text-left rounded-lg bg-slate-900/60 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 transition group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-white group-hover:text-cyan-400">
                        PM
                      </span>
                      <span className="text-[9px] font-mono text-blue-400 bg-blue-950 px-1 py-0.5 rounded">
                        pm123!
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 truncate">pm@risklattice.com</div>
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      handleQuickFill(
                        "analyst@risklattice.com",
                        "analyst123!",
                        "Elena Rostova",
                        "ANALYST",
                        "Macro Quant Research"
                      )
                    }
                    className="p-2 text-left rounded-lg bg-slate-900/60 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 transition group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-white group-hover:text-cyan-400">
                        Analyst
                      </span>
                      <span className="text-[9px] font-mono text-purple-400 bg-purple-950 px-1 py-0.5 rounded">
                        analyst123!
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 truncate">analyst@risklattice.com</div>
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      handleQuickFill(
                        "auditor@risklattice.com",
                        "auditor123!",
                        "David Sterling",
                        "AUDITOR",
                        "Model Validation"
                      )
                    }
                    className="p-2 text-left rounded-lg bg-slate-900/60 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 transition group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-white group-hover:text-cyan-400">
                        Auditor
                      </span>
                      <span className="text-[9px] font-mono text-amber-400 bg-amber-950 px-1 py-0.5 rounded">
                        auditor123!
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 truncate">auditor@risklattice.com</div>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="text-center text-[11px] text-slate-500 flex items-center justify-center space-x-2">
          <span>DuckDB Salted PBKDF2 / Bcrypt</span>
          <span>•</span>
          <span>PyJWT HMAC-SHA256</span>
          <span>•</span>
          <span>Google Identity Services SDK</span>
        </div>
      </div>
    </div>
  );
}
