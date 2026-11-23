# RiskLattice Feature Documentation Index

Welcome to the definitive feature documentation repository for **RiskLattice**, the institutional-grade neuro-symbolic cross-asset macro contagion stress-testing platform.

RiskLattice pairs a deterministic, non-linear Python quantitative math engine with an LLM-assisted semantic orchestration layer to simulate cascade transmission across multi-tier supply chains, capital structures, and geopolitical choke points.

---

## Complete Feature Matrix

| # | Feature Name | Core Methodology | Primary Files | Status |
|---|---|---|---|---|
| **01** | [Multi-Hop Contagion Engine](./01_multi_hop_contagion_engine.md) | 4-hop damped propagation via SciPy CSR sparse matrix $W$, attenuation decay $\lambda$, non-linear distress amplification | `backend/app/engine/propagator.py` | Production |
| **02** | [Student-t Copula Tail-Risk Engine](./02_student_t_copula_tail_risk.md) | Heavy-tailed joint distributions ($\nu = 4.0$), Higham PSD repair, Cholesky factorization, 10k Monte Carlo paths | `backend/app/engine/risk_metrics.py` | Production |
| **03** | [Multi-Asset Non-Linear Valuation](./03_multi_asset_valuation.md) | Derivatives (Black-Scholes Greeks), Corporate Bonds (Duration/Convexity/Merton), CDS (hazard rate jump), Private Credit, FX, CLO tranches | `backend/app/engine/instruments.py` | Production |
| **04** | [Expanded Systemic Factors](./04_expanded_systemic_factors.md) | 12 systemic risk channels: Maritime Choke Points (Taiwan Strait, Malacca, Suez), Banking Plumbing (SOFR, Repo, Basis), Operational Shocks | `backend/app/engine/factors.py` | Production |
| **05** | [Safety Stock Inventory Buffers](./05_safety_stock_inventory_buffers.md) | Dynamic inventory absorption: $S_{\text{eff}} = \max(0, S_{\text{gross}} \cdot (1 - \text{Days}_{\text{Inv}} / \text{Duration}))$, buffer depletion kinetics | `backend/app/engine/propagator.py` | Production |
| **06** | [Tail-Risk Hedge Optimizer](./06_tail_risk_hedge_optimizer.md) | Mixed-Integer Programming (MILP/MIQP) minimizing downside CVaR under budget constraints with basis risk penalty | `backend/app/engine/optimizer.py` | Production |
| **07** | [Reverse Stress Testing](./07_reverse_stress_testing.md) | Algorithmic inverse solver finding minimal shock vector $s^*$ that breaches target portfolio drawdown | `backend/app/engine/optimizer.py` | Production |
| **08** | [Multi-Period Timeline Simulation](./08_multi_period_timeline_simulation.md) | Discrete-time simulation ($T \in [0, 90]$ days) with lead-time delays, safety stock exhaustion, and order backlog cascades | `backend/app/engine/timeline.py` | Production |
| **09** | [Scenario Diffing & A/B Attribution](./09_scenario_diffing_and_ab_attribution.md) | Side-by-side scenario comparison, Shapley / Euler marginal risk decomposition, and hop-by-hop delta waterfall | `backend/app/engine/diffing.py` | Production |
| **10** | [Board-Ready Executive Memo Generator](./10_board_ready_executive_memo.md) | Automated C-suite stress briefing with Markdown, HTML, and PDF export formatting regulatory disclosures and mitigation actions | `backend/app/services/report_generator_service.py` | Production |
| **11** | [Four-Eyes Governance & Audit Vault](./11_four_eyes_audit_vault.md) | Cryptographic SHA-256 audit trail, dual-key signoff workflow (Draft $\to$ Under Review $\to$ Approved), Basel III / SR 11-7 compliance | `backend/app/services/audit_vault_service.py` | Production |
| **12** | [Google Workspace SSO & RBAC](./12_google_workspace_sso_and_rbac.md) | Institutional OAuth2 authentication with JWT verification and 4-tier role-based access control (CRO, PM, Analyst, Auditor) | `backend/app/services/auth_service.py` | Production |
| **13** | [Endogenous Market Impact & Liquidity](./13_endogenous_market_impact_and_liquidity.md) | Almgren-Chriss (2000) optimal liquidation, temporary/permanent slippage, fire-sale feedback $\xi$, and ISDA SIMM margin call spiral | `backend/app/engine/liquidity.py` | Production |
| **14** | [Autonomous SEC EDGAR 10-K/8-K Crawler](./14_autonomous_sec_edgar_crawler.md) | Continuous SEC crawler polling Forms 10-K, 10-Q, 8-K with verbatim quote matching and confidence-scored supply chain edge discovery | `backend/app/services/edgar_crawler_service.py` | Production |
| **15** | [Interactive Geospatial World Map](./15_interactive_geospatial_world_map.md) | Interactive WGS84 Mercator projection of fab clusters, maritime straits, global container ports, and critical logistics corridors | `frontend/src/components/GeospatialMap.tsx` | Production |
| **16** | [PMS/OMS Adapters & Fed CCAR Exporter](./16_pms_oms_adapters_and_ccar_exporter.md) | BlackRock Aladdin CSV parser, Bloomberg PORT JSON adapter, and Federal Reserve Form FR Y-14A Schedule A export generator | `backend/app/services/institutional_adapters_service.py` | Production |
| **17** | [What-If Supply Chain Graph Mutation](./17_what_if_graph_mutation_engine.md) | Network intervention modeling (sever, add, reweight edges), Resilience ROI ($\Delta\text{PnL} / \text{CapEx}$), and regulatory capital relief | `backend/app/engine/mutation.py` | Production |
| **18** | [AI Conversational Stress Copilot](./18_ai_stress_copilot.md) | Real-time conversational risk assistant with natural language query routing, exact metrics computation, and SEC 10-K grounding | `backend/app/agents/stress_copilot.py` | Production |
| **19** | [Multi-Channel Webhook Alerting](./19_webhook_alerting_system.md) | Real-time risk appetite limit breach evaluation, Slack Block Kit formatting, Microsoft Teams cards, and PagerDuty incident dispatch | `backend/app/services/alerting_service.py` | Production |
| **20** | [Live Threat Intel & AIS Maritime Simulator](./20_live_threat_intel_and_ais_simulator.md) | Real-time satellite AIS vessel congestion across 5 choke points, Systemic Vulnerability Index (SVI), threat wire feed & 1-click shock injection | `backend/app/engine/ais_threat.py` | Production |
| **21** | [Adversarial Chaos Engineering & Circuit Breakers](./21_chaos_engineering_and_circuit_breakers.md) | 3-state Gateway Circuit Breakers (Closed/Open/Half-Open), pure AST chaos generators (cyclic graphs, singular covariance, leverage cliffs), & automated CLI chaos drill | `backend/app/engine/chaos.py`<br>`backend/app/services/circuit_breaker_service.py` | Production |

---

## Architectural Principles

1. **Deterministic AST Boundary (ADR-002)**:
   All quantitative engine files under `backend/app/engine/*.py` are pure compute functions and must NEVER import network clients, databases, or LLMs (`httpx`, `requests`, `duckdb`, `fastapi`, `litellm`). This guarantee is verified in CI via `test_engine_ast_import_isolation`.
2. **Verbatim Audit Trail (ADR-003)**:
   Every graph edge extracted from unstructured filings includes character-offset citations and exact verbatim quotes from SEC 10-K disclosures, preventing LLM hallucinations.
3. **Dual-Key Governance (SR 11-7)**:
   Institutional stress test runs require independent verification and immutable SHA-256 digital signatures before submission to the Board of Directors or regulatory authorities.
