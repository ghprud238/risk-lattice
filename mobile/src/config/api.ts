import { Platform } from "react-native";
import {
  ThreatSnapshot,
  SimulateResponse,
  AuditEntry,
  CopilotResponse,
  UserProfile,
} from "../types";

// Default localhost depending on environment:
// iOS Simulator uses localhost; Android Emulator uses 10.0.2.2.
const DEFAULT_HOST = Platform.OS === "android" ? "http://10.0.2.2:5051" : "http://localhost:5051";

let currentApiBase = DEFAULT_HOST;

export const setApiBaseUrl = (url: string) => {
  currentApiBase = url.replace(/\/+$/, "");
};

export const getApiBaseUrl = () => currentApiBase;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${currentApiBase}${path}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 12000);

  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(options.headers || {}),
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`HTTP ${res.status}: ${errText || res.statusText}`);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new Error(`Connection to ${url} timed out (12s). Ensure backend is running on :5051.`);
    }
    throw err;
  }
}

export const api = {
  checkHealth: async () => {
    return request<{ status: string; total_nodes: number; total_edges: number }>("/api/v1/health");
  },

  getThreatStatus: async (): Promise<ThreatSnapshot> => {
    return request<ThreatSnapshot>("/api/v1/threats/ais/status");
  },

  advanceThreatTick: async (): Promise<ThreatSnapshot> => {
    return request<ThreatSnapshot>("/api/v1/threats/ais/tick", { method: "POST" });
  },

  injectThreat: async (eventId: string): Promise<any> => {
    return request<any>("/api/v1/threats/inject", {
      method: "POST",
      body: JSON.stringify({ event_id: eventId }),
    });
  },

  runSimulation: async (payload: {
    scenario_name?: string;
    scenario_prompt?: string;
    direct_impulses?: Record<string, number>;
    portfolio_weights?: Record<string, number>;
  }): Promise<SimulateResponse> => {
    return request<SimulateResponse>("/api/v1/stress/simulate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  askCopilot: async (
    query: string,
    portfolioNotional: number = 100_000_000,
    unhedgedPnl: number = -22_400_000,
    nodeShocks?: Record<string, number>
  ): Promise<CopilotResponse> => {
    return request<CopilotResponse>("/api/v1/copilot/chat", {
      method: "POST",
      body: JSON.stringify({
        query,
        portfolio_notional: portfolioNotional,
        unhedged_pnl: unhedgedPnl,
        node_shocks: nodeShocks,
      }),
    });
  },

  getAuditEntries: async (): Promise<{ entries: AuditEntry[] }> => {
    return request<{ entries: AuditEntry[] }>("/api/v1/audit/entries");
  },

  approveAuditRun: async (
    runId: string,
    approverEmail: string,
    approverRole: string,
    comments?: string
  ): Promise<{ entry: AuditEntry }> => {
    return request<{ entry: AuditEntry }>("/api/v1/audit/approve", {
      method: "POST",
      body: JSON.stringify({
        run_id: runId,
        approver_email: approverEmail,
        approver_role: approverRole,
        comments,
      }),
    });
  },

  authenticateSandboxPersona: async (persona: string): Promise<{ token: string; user: UserProfile }> => {
    return request<{ token: string; user: UserProfile }>("/api/v1/auth/google", {
      method: "POST",
      body: JSON.stringify({ persona }),
    });
  },
};
