# RiskLattice Documentation Hub

Welcome to the engineering documentation hub for **RiskLattice**, the institutional-grade neuro-symbolic financial stress-testing platform.

RiskLattice pairs a deterministic, non-linear Python quantitative math engine with an LLM-assisted semantic orchestration layer to simulate cascade transmission across multi-tier supply chains, capital structures, and geopolitical choke points.

---

## Documentation Directory Map

```
docs/
├── README.md                                  <-- Master Documentation Hub (This File)
├── adrs/                                      <-- Architecture Decision Records (ADR-001 to ADR-010)
│   ├── ADR-001-storage.md                     <-- Embedded DuckDB OLAP Storage
│   ├── ADR-002-compute.md                     <-- Pure Compute Engine Isolation Boundary
│   ├── ADR-003-graph.md                       <-- 4-Hop Damped Contagion Propagation
│   ├── ADR-004-model.md                       <-- Huber Loss Robust Linear Calibration
│   ├── ADR-005-risk.md                        <-- 10,000-Path Student-t Copula Simulation
│   ├── ADR-006-ai.md                          <-- Neuro-Symbolic Boundary & Local Privacy Firewall
│   ├── ADR-007-native.md                      <-- Python Subprocess Minsky Integration
│   ├── ADR-008-deploy.md                      <-- Next.js 15 & FastAPI Deployment on Ports 5050/5051
│   ├── ADR-009-time.md                        <-- Snapshot-Based Time & Decay Model
│   └── ADR-010-pdf.md                         <-- Server-Side PDF & Executive Report Generation
├── features/                                  <-- Exhaustive Feature Guides (Features 01 to 20)
│   ├── README.md                              <-- Master Feature Matrix & Catalog
│   ├── 01_multi_hop_contagion_engine.md       <-- 4-Hop Damped Contagion Propagation
│   ├── 02_student_t_copula_tail_risk.md       <-- Student-t Copula & 99% CVaR
│   ├── 03_multi_asset_valuation.md            <-- Multi-Asset Derivatives & Bond Pricing
│   ├── 04_expanded_systemic_factors.md        <-- 12 Systemic Macro Factors & Choke Points
│   ├── 05_safety_stock_inventory_buffers.md   <-- Days-of-Inventory Absorption Kinetics
│   ├── 06_tail_risk_hedge_optimizer.md        <-- MILP/MIQP Capital-Efficient Hedge Allocator
│   ├── 07_reverse_stress_testing.md           <-- Algorithmic Minimal Breaking Point Solver
│   ├── 08_multi_period_timeline_simulation.md <-- 0-90 Day Dynamic Wave Propagation
│   ├── 09_scenario_diffing_and_ab_attribution.md <-- Side-by-Side Diffing & Shapley Attribution
│   ├── 10_board_ready_executive_memo.md       <-- C-Suite Memo & PDF Generator
│   ├── 11_four_eyes_audit_vault.md            <-- Cryptographic SHA-256 Dual-Key Sign-off
│   ├── 12_google_workspace_sso_and_rbac.md    <-- Google OAuth2 & 4-Tier Institutional RBAC
│   ├── 13_endogenous_market_impact_and_liquidity.md <-- Almgren-Chriss Slippage & Margin Spiral
│   ├── 14_autonomous_sec_edgar_crawler.md     <-- Continuous 10-K/8-K Feed & Verbatim Matching
│   ├── 15_interactive_geospatial_world_map.md <-- SVG Mercator World Map & Transit Arcs
│   ├── 16_pms_oms_adapters_and_ccar_exporter.md <-- Aladdin/PORT Adapters & Fed CCAR FR Y-14A
│   ├── 17_what_if_graph_mutation_engine.md    <-- Network Interventions & Resilience ROI
│   ├── 18_ai_stress_copilot.md                <-- Conversational CRO Assistant
│   ├── 19_webhook_alerting_system.md          <-- Slack Block Kit Multi-Channel Webhooks
│   └── 20_live_threat_intel_and_ais_simulator.md <-- Live Satellite AIS Radar & Threat Feed
└── daily_notes/                               <-- Chronological Engineering & Quantitative Logs
    ├── README.md                              <-- Master Index of Daily Notes
    ├── 2026-11-10.md                          <-- Milestones 1–4, DuckDB, Huber, AST Isolation
    ├── 2026-11-11.md                          <-- Taiwan Foundry Walkthrough, 5-Tier Data Flow
    ├── 2026-11-12.md                          <-- Dockerization, Ports 5050/5051, B2B Competitive Teardown
    ├── 2026-11-13.md                          <-- Multi-Asset Pricing, 12 Factors, Inventory Buffers
    ├── 2026-11-14.md                          <-- Google SSO, Hedge Optimizer, Reverse Stress, Timeline
    ├── 2026-11-15.md                          <-- Almgren-Chriss Liquidity, What-If Mutation, 19 Features
    └── 2026-11-16.md                          <-- Live Threat Intel, Satellite AIS Simulator, SVI Index
```

---

## Architectural Principles & Data Flows

1. **Deterministic AST Boundary ([ADR-002](./adrs/ADR-002-compute.md))**:
   All quantitative engine files under `backend/app/engine/*.py` are pure compute functions and must NEVER import network clients, databases, or LLMs (`httpx`, `requests`, `duckdb`, `fastapi`, `litellm`). This guarantee is verified in CI via `test_engine_ast_import_isolation`.
2. **End-to-End Taiwan Foundry Data Flow ([2026-11-11 Notes](./daily_notes/2026-11-11.md#3-end-to-end-operational-walkthrough-the-taiwan-foundry-cascade))**:
   Traces a semiconductor disruption impulse from raw natural language prompt through vector translation, 4-hop sparse CSR propagation, Student-$t$ Copula Monte Carlo sampling, portfolio valuation, and SEC 10-K citation matching.
3. **Verbatim Audit Trail ([ADR-003](./adrs/ADR-003-graph.md) & [ADR-006](./adrs/ADR-006-ai.md))**:
   Every graph edge extracted from unstructured filings includes character-offset citations and exact verbatim quotes from SEC 10-K disclosures, preventing LLM hallucinations.
4. **Dual-Key Governance & Cryptographic Vault ([ADR-010](./adrs/ADR-010-pdf.md) & [Feature 11](./features/11_four_eyes_audit_vault.md))**:
   Institutional stress test runs produce immutable SHA-256 digital seals requiring independent secondary sign-off before submission to bank regulators (Federal Reserve SR 11-7 compliance).

---

## Quick Command Verification

```bash
cd /Users/dpcubed/projects/risk-lattice

# 1. Environment & System Doctor
.venv/bin/python backend/scripts/doctor.py

# 2. Ultra-Fast Offline Math Smoke Test (0.126s)
.venv/bin/python backend/scripts/smoke_test.py

# 3. Privacy Firewall Red-Team Audit (Rule P-01)
.venv/bin/python backend/scripts/verify_privacy.py

# 4. AST Isolation Boundary Check
uv run pytest backend/tests/integration/test_boundary_and_engine.py -v

# 5. Complete 95-Test Suite
uv run pytest backend/tests/ -v
```
