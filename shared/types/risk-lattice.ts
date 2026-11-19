/**
 * RiskLattice Shared TypeScript Type Definitions
 * Single source of truth for Web (React / Next.js) and Mobile (React Native / Expo).
 * Based on docs/use_cases_data_specification.md.
 */

export type SeverityLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type SviStatus = "NORMAL" | "ELEVATED" | "SEVERE" | "CRITICAL";

export type UserRole = "CHIEF_RISK_OFFICER" | "PORTFOLIO_MANAGER" | "RISK_ANALYST" | "AUDITOR";

export interface ChokePointTelemetry {
  choke_point_id: string;
  name: string;
  active_vessels: number;
  baseline_vessels: number;
  median_speed_knots: number;
  baseline_speed_knots: number;
  congestion_index: number;
  demurrage_surge_pct: number;
  disruption_prob: number;
  status: SviStatus;
  criticality_weight: number;
}

export interface ThreatEvent {
  event_id: string;
  headline: string;
  source: string;
  severity: SeverityLevel;
  choke_point_id: string;
  timestamp: string;
  affected_nodes: string[];
  raw_supply_impact_pct: number;
  details: string;
  decay_weight: number;
}

export interface ThreatSnapshot {
  svi_index: number;
  svi_status: SviStatus;
  active_threats_count: number;
  choke_points: ChokePointTelemetry[];
  recent_threats: ThreatEvent[];
  timestamp: string;
}

export interface PortfolioPnL {
  hop1_pnl: number;
  hop2_pnl: number;
  hop3_4_pnl: number;
  total_pnl: number;
  drawdown_pct: number;
}

export interface NodeShockDetail {
  direct_shock: number;
  hop1_shock: number;
  hop2_shock: number;
  hop3_4_shock: number;
  cumulative_shock: number;
  status: "HEALTHY" | "ALERT" | "SEVERE_DISTRESS";
  distress_multiplier: number;
}

export interface RiskMetricsResult {
  var_95: number;
  cvar_99: number;
  tail_ratio: number;
  marginal_risk: Record<string, number>;
}

export interface NarrativeReport {
  macro_trigger: string;
  bottleneck_summary: string;
  hedge_recommendation: string;
}

export interface SimulationResult {
  scenario_name: string;
  portfolio_pnl: PortfolioPnL;
  node_shocks: Record<string, NodeShockDetail>;
  critical_paths: string[][];
}

export interface SimulateResponse {
  simulation: SimulationResult;
  risk_metrics: RiskMetricsResult;
  narrative: NarrativeReport;
}

export interface AuditEntry {
  run_id: string;
  scenario_name: string;
  submitted_by: string;
  submitted_by_role: string;
  pnl_impact: number;
  cvar_99: number;
  shock_summary: Record<string, number>;
  status: "DRAFT" | "UNDER_REVIEW" | "APPROVED" | "LOCKED";
  primary_signature?: string;
  primary_signed_at?: string;
  secondary_signature?: string;
  secondary_signed_at?: string;
  sha256_seal?: string;
  timestamp: string;
  comments?: string;
}

export interface CopilotCitation {
  source: string;
  quote: string;
  chunk_id?: string;
}

export interface CopilotResponse {
  query: string;
  intent: string;
  answer: string;
  cited_nodes: string[];
  citations: CopilotCitation[];
  recommendations: string[];
}

export interface UserProfile {
  user_id: string;
  email: string;
  name: string;
  role: UserRole;
  organization: string;
  permissions: string[];
}
