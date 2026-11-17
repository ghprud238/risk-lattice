# RiskLattice: Use Cases Input & Output Data Specification

This document provides a comprehensive, institutional-grade data dictionary and technical specification of the **Inputs and Outputs for all 19 Operational Use Cases** across the RiskLattice financial stress-testing platform.

It is designed for Chief Risk Officers (CROs), quantitative risk developers, model validation auditors (SR 11-7 / Basel III), and enterprise data engineers integrating RiskLattice with institutional PMS/OMS platforms (BlackRock Aladdin, Bloomberg PORT, SimCorp Dimension).

---

## Master Data Architecture & Schema Taxonomy

RiskLattice enforces a strict **neuro-symbolic boundary** ([ADR-002](adrs/ADR-002-compute.md) and [ADR-006](adrs/ADR-006-ai.md)):
1. **Inputs Tier**: Ingests multi-modal data (geopolitical prompts, 12 systemic macro factors, 7 multi-asset position ledgers, SEC EDGAR 10-K/8-K disclosures, satellite AIS vessel transponders, and historical 504-day returns).
2. **Deterministic Engine Tier**: AST-isolated Python compute functions executing Huber loss regression, 4-hop sparse CSR propagation, non-linear leverage distress ($\lambda_v, \mu$), 10,000-path Student-$t$ Copula Monte Carlo, Almgren-Chriss market impact, and MILP/MIQP optimization.
3. **Outputs Tier**: Delivers bit-exact PnL waterfall ledgers, coherent 99% Expected Shortfall (CVaR), Marginal Contribution to Risk (MCR), real-time SSE animation streams, board-ready executive memos (PDF/HTML), and SHA-256 cryptographic audit seals.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   INPUT / OUTPUT DATA FLOW TAXONOMY                                    │
├─────────────────────────────────────────────────┬──────────────────────────────────────────────────────┤
│                     INPUT DATA                  │                      OUTPUT DATA                     │
├─────────────────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ • Natural Language Prompts (Free-form English)  │ • Hop-by-Hop Node Shock Vectors (0 to 4 hops)        │
│ • 12 Systemic Macro Factors (Clamped bounds)    │ • 3-Stage PnL Waterfall (1st, 2nd, 3rd/4th order)     │
│ • 7 Asset Class Holdings (CSV/JSON/Aladdin)     │ • 99% VaR, 99% CVaR & Tail Ratio (Copula vs Normal)  │
│ • SEC EDGAR 10-K/8-K Chunks (Item 1A / Footnotes│ • Marginal Contribution to Risk (MCR per ticker)     │
│ • Live Satellite AIS Telemetry (5 Choke Points) │ • Real-Time SSE Stream Events (started -> completed) │
│ • 504-Day 2-Regime Market Return Matrices       │ • Almgren-Chriss Slippage & SIMM Margin Call Drain   │
│ • Balance Sheet Fundamentals (NetDebt, ICR, DOI)│ • Board-Ready Memos (Markdown/HTML/PDF) & CCAR Packet│
│ • Four-Eyes Dual Signatures & Google OAuth2 JWT │ • SHA-256 Cryptographic Audit Manifest (SR 11-7)     │
└─────────────────────────────────────────────────┴──────────────────────────────────────────────────────┘
```

---

## Master Use Case Index & Quick Reference

| UC # | Use Case Name | Primary Endpoints | Key Input Data | Key Output Artifacts | Primary Persona |
|:---:|---|---|---|---|:---:|
| **01** | [Geopolitical Semiconductor & Maritime Halt](#uc-01-geopolitical-semiconductor--maritime-disruption) | `POST /api/v1/stress/simulate`<br>`GET /api/v1/stress/stream` | Shock factors (`FOUNDRY_TW`, `BALTIC_DRY`), Portfolio weights | Hop 0-4 node shocks, PnL waterfall, 99% CVaR, SEC citations | CRO / Head of Risk |
| **02** | [Historical Crisis Replay & Regulatory Benchmarking](#uc-02-historical-crisis-replay--regulatory-benchmarking) | `POST /api/v1/backtest/run`<br>`POST /api/v1/backtest/replay` | Scenario ID (`2008_GFC`, `2020_COVID`, `2022_DURATION`, `2021_SUEZ`) | Kupiec POF $\chi^2$ statistic, 2nd-order recall, realized vs simulated drawdown | Model Validation Auditor |
| **03** | [Natural Language Free-Form Scenario Authoring](#uc-03-natural-language-free-form-scenario-authoring) | `POST /api/v1/scenarios/draft`<br>`POST /api/v1/stress/simulate` | Plain-English prompt text | Sanitized text, clamped factor shocks, canonical factor mapping | Senior Portfolio Manager |
| **04** | [SEC 10-K Verbatim Dependency Extraction](#uc-04-sec-10-k-verbatim-dependency-graph-extraction) | `POST /api/v1/graph/extract`<br>`POST /api/v1/edgar/ingest` | 10-K filing chunk text, company ticker | Extracted edges, character offsets, verbatim quote match | Quantitative Research Analyst |
| **05** | [Institutional Multi-Asset Convexity Valuation](#uc-05-institutional-multi-asset-portfolio-convexity-valuation) | `POST /api/v1/portfolio/ingest`<br>`POST /api/v1/portfolios/{id}/versions` | 7-asset holdings ledger (Equities, Options, Bonds, CDS, Credit, FX, CLO) | Non-linear PnL, duration/convexity shift, credit spread widening | Multi-Asset Portfolio Manager |
| **06** | [Capital-Constrained Tail-Risk Hedge Optimizer](#uc-06-capital-constrained-tail-risk-hedge-optimizer) | `POST /api/v1/optimize/hedge` | Portfolio notional, unhedged PnL, node shocks, budget limit | Optimal hedge allocation, hedged CVaR, basis risk penalty, frontier | Derivatives Structurer / Hedging Desk |
| **07** | [Algorithmic Reverse Stress Testing](#uc-07-algorithmic-reverse-stress-testing) | `POST /api/v1/stress/reverse` | Target loss % ($D_{\text{target}}$), factor sensitivities | Minimal $L_2$ shock vector $\mathbf{s}^*$, critical factor, vulnerable nodes | Regulatory Capital Officer |
| **08** | [Multi-Period Forward Timeline Simulation](#uc-08-multi-period-forward-timeline-simulation-0-90-days) | `POST /api/v1/stress/timeline` | Initial shocks, time horizon (0-90 days), Days of Inventory (DOI) | Daily shock trajectory, inventory depletion day, milestone log | Supply Chain & Credit Analyst |
| **09** | [Scenario Diffing & Shapley/Euler Attribution](#uc-09-scenario-diffing--shapleyeuler-attribution) | `POST /api/v1/scenario/diff` | Baseline scenario (A), Stressed scenario (B), positions | Delta PnL, delta CVaR, node status shifts, Shapley factor contributions | Senior Risk Committee |
| **10** | [Endogenous Liquidity & Fire-Sale Margin Spirals](#uc-10-endogenous-liquidity-almgren-chriss-slippage--margin-spirals) | `POST /api/v1/liquidity/simulate` | Asset positions, ADV, volatility, liquidation %, cash balance | Almgren-Chriss slippage, fire-sale feedback $\xi$, SIMM margin calls | Chief Liquidity Officer / Treasurer |
| **11** | [What-If Supply Chain Graph Mutation Studio](#uc-11-what-if-supply-chain-graph-mutation-studio) | `POST /api/v1/mutation/evaluate` | Graph mutation actions (sever, add, reweight), CapEx cost | Stressed $\Delta\text{PnL}$, Resilience ROI, Pillar 2 capital relief | Strategic Sourcing & CapEx Committee |
| **12** | [Live Satellite AIS Maritime Telemetry & Threat Ingestion](#uc-12-live-satellite-ais-telemetry--threat-injection) | `GET /api/v1/threats/ais/status`<br>`POST /api/v1/threats/inject` | AIS telemetry transponder ticks, military threat wire events | Congestion index $C$, demurrage surge, SVI ($0-100$), decaying shock impulses | Geopolitical Intelligence Analyst |
| **13** | [Autonomous SEC EDGAR Continuous Crawler](#uc-13-autonomous-sec-edgar-continuous-crawler) | `GET /api/v1/edgar/status`<br>`POST /api/v1/edgar/ingest` | Ticker, filing type (10-K, 10-Q, 8-K), accession number | Discovered counterparty links, confidence score, DuckDB edge update | Data Operations Engineer |
| **14** | [Interactive Geospatial Physical Lattice](#uc-14-interactive-geospatial-physical-lattice) | `GET /api/v1/graph/geospatial` | N/A (Internal geospatial facility & choke point registry) | WGS84 facility coordinates, transit arcs, criticality weights | Supply Chain Operations |
| **15** | [PMS/OMS Ingestion & Fed CCAR Form FR Y-14A Export](#uc-15-pmsoms-ingestion--fed-ccar-fr-y-14a-export) | `POST /api/v1/pms/aladdin/import`<br>`POST /api/v1/regulatory/ccar/export` | BlackRock Aladdin CSV / Bloomberg PORT JSON | Standardized portfolio, Schedule A Form FR Y-14A export packet | Regulatory Reporting Desk |
| **16** | [Conversational AI Chief Risk Officer Copilot](#uc-16-conversational-ai-chief-risk-officer-copilot) | `POST /api/v1/copilot/chat` | Natural language question, active scenario state, portfolio context | Parsed intent, calculated risk metrics, grounded SEC 10-K citations | Board of Directors / Executives |
| **17** | [Multi-Channel Webhook Alerting & Incident Dispatch](#uc-17-multi-channel-webhook-alerting--incident-dispatch) | `GET /api/v1/alerts`<br>`POST /api/v1/alerts/test` | Threshold limits (drawdown %, CVaR $), scenario results | Slack Block Kit payload, Teams card, PagerDuty incident payload | Enterprise Operations / SRE |
| **18** | [Executive Memo Generator & Four-Eyes Cryptographic Audit](#uc-18-executive-memo-generator--four-eyes-cryptographic-audit) | `POST /api/v1/report/executive`<br>`POST /api/v1/audit/approve` | Run ID, reviewer sign-offs, CRO credentials, commentary | C-suite memo (MD/HTML/PDF), SHA-256 digital seal, signed audit entry | Chief Risk Officer / Internal Audit |
| **19** | [Google Workspace Enterprise SSO & 4-Tier RBAC](#uc-19-google-workspace-enterprise-sso--4-tier-rbac) | `POST /api/v1/auth/google`<br>`GET /api/v1/auth/me` | Google OAuth2 ID token / sandbox persona selection | Validated JWT session, user role (`CRO`, `PM`, `ANALYST`, `AUDITOR`) | Enterprise IAM Administrator |

---

## Exhaustive Use Case Data Specifications

---

### UC-01: Geopolitical Semiconductor & Maritime Disruption

#### 1. Business Context & Objective
Simulates the systemic impact of a geopolitical event in the Taiwan Strait that halts advanced semiconductor wafer exports while disrupting maritime shipping through global choke points. Propagates shocks across 4 network hops and revalues portfolios under extreme tail correlation breakdown.

#### 2. Primary Endpoints
- `POST /api/v1/stress/simulate` (Synchronous full simulation)
- `GET /api/v1/stress/stream` (Server-Sent Events streaming hop-by-hop updates)

#### 3. Input Data Specification

| Parameter | Type | Unit | Range / Constraints | Req? | Description |
|---|---|---|---|:---:|---|
| `scenario_name` | `string` | UTF-8 | 1 - 100 chars | Optional | Descriptive scenario title |
| `scenario_prompt` | `string` | Text | Max 500 chars | Optional* | Natural language scenario description (mutually exclusive with `direct_impulses`) |
| `direct_impulses` | `object` | Fraction | Keys: factor/node IDs; Values: $[-0.95, +2.00]$ | Optional* | Initial impulse shock vector ($s^{(0)}$) |
| `portfolio_weights` | `object` | Fraction | Keys: tickers; Values: $[0.0, 1.0]$, $\sum = 1.0$ | Optional | Portfolio asset allocations (defaults to canonical 5-asset mix) |

*Either `scenario_prompt` or `direct_impulses` must be provided.

**Sample Request Payload (`POST /api/v1/stress/simulate`)**:
```json
{
  "scenario_name": "Taiwan Strait Naval Quarantine & Maritime Spike",
  "direct_impulses": {
    "FOUNDRY_TW": -0.70,
    "BALTIC_DRY": 1.80,
    "BRENT_CRUDE": 0.45,
    "SOFR_SPREAD": 0.035
  },
  "portfolio_weights": {
    "NVDA": 0.25,
    "TSM": 0.20,
    "AAPL": 0.20,
    "F": 0.15,
    "MSFT": 0.20
  }
}
```

#### 4. Output Data Specification

| Field Path | Type | Unit | Description |
|---|---|---|---|
| `simulation.scenario_name` | `string` | Text | Name of the evaluated scenario |
| `simulation.hop_progression` | `array[object]` | Metrics | Cumulative activation counts and energy at Hops 0, 1, 2, 3, 4 |
| `simulation.node_shocks` | `object` | Fraction | Map of node IDs to detailed shock metrics (`direct_shock`, `hop1_shock`, `hop2_shock`, `hop3_4_shock`, `cumulative_shock`, `status`, `distress_multiplier`) |
| `simulation.portfolio_pnl` | `object` | USD / % | Decomposed PnL waterfall (`hop1_pnl`, `hop2_pnl`, `hop3_4_pnl`, `total_pnl`, `drawdown_pct`) |
| `simulation.critical_paths` | `array[string]` | Path | Primary transmission paths driving the largest losses |
| `risk_metrics.var_95` | `float` | Fraction | Parametric 95% Value at Risk |
| `risk_metrics.cvar_99` | `float` | Fraction | Heavy-tailed 99% Expected Shortfall via Student-$t$ Copula |
| `risk_metrics.tail_ratio` | `float` | Ratio | Ratio of Copula CVaR to Gaussian VaR ($>1.0$ indicates tail underestimation) |
| `risk_metrics.marginal_risk` | `object` | Fraction | Position-by-position Marginal Contribution to Risk (MCR) |
| `narrative.macro_trigger` | `string` | Text | Plain-English summary of the initiating geopolitical shock |
| `narrative.bottleneck_summary` | `string` | Text | Explanation of critical transmission nodes with `[10-K Chunk #ID]` citations |
| `narrative.hedge_recommendation`| `string` | Text | Concrete actionable hedges |

**Sample Response Payload**:
```json
{
  "simulation": {
    "scenario_name": "Taiwan Strait Naval Quarantine & Maritime Spike",
    "portfolio_pnl": {
      "hop1_pnl": -35000000.0,
      "hop2_pnl": -53500000.0,
      "hop3_4_pnl": -12300000.0,
      "total_pnl": -100800000.0,
      "drawdown_pct": -0.224
    },
    "node_shocks": {
      "TSM": {
        "cumulative_shock": -0.70,
        "status": "SEVERE_DISTRESS",
        "distress_multiplier": 1.0
      },
      "NVDA": {
        "cumulative_shock": -0.535,
        "status": "SEVERE_DISTRESS",
        "distress_multiplier": 1.0
      },
      "F": {
        "cumulative_shock": -0.231,
        "status": "SEVERE_DISTRESS",
        "distress_multiplier": 1.63
      }
    },
    "critical_paths": [
      "FOUNDRY_TW -> TSM -> NVDA -> MSFT",
      "FOUNDRY_TW -> TSM -> NXP -> F"
    ]
  },
  "risk_metrics": {
    "var_95": 0.0641,
    "cvar_99": 0.2552,
    "tail_ratio": 12.21,
    "marginal_risk": {
      "NVDA": 0.482,
      "TSM": 0.314,
      "AAPL": 0.112,
      "F": 0.062,
      "MSFT": 0.030
    }
  },
  "narrative": {
    "macro_trigger": "Taiwanese wafer export volumes dropped 70.0% and Baltic Dry freight surged 180.0%.",
    "bottleneck_summary": "TSMC wafer shortages immediately choked Nvidia GPU packaging and Ford microcontroller modules [10-K Chunk #14]. Ford's NetDebt/EBITDA of 4.8 triggered leverage distress lambda=1.63x.",
    "hedge_recommendation": "Purchase SOXX 3-month 15% OTM put options and long Baltic Dry freight index swaps."
  }
}
```

---

### UC-02: Historical Crisis Replay & Regulatory Benchmarking

#### 1. Business Context & Objective
Replays pinned historical crisis regimes to benchmark RiskLattice against realized market drawdowns. Runs the **Kupiec Proportion of Failures (POF)** statistical test ($\chi_1^2$ likelihood ratio) to ensure model conservatism for regulatory capital adequacy (Basel III Pillar 1/2).

#### 2. Primary Endpoints
- `POST /api/v1/backtest/run` (Executes single or all historical scenarios)
- `POST /api/v1/backtest/replay` (Synchronous replay by benchmark identifier)

#### 3. Input Data Specification

| Parameter | Type | Allowed Values | Req? | Description |
|---|---|---|:---:|---|
| `scenario_id` | `string` | `"all"`, `"2008_GFC"`, `"2020_COVID"`, `"2022_DURATION"`, `"2021_SUEZ"` | Yes | Identifier of historical benchmark to evaluate |

**Sample Request Payload (`POST /api/v1/backtest/run`)**:
```json
{
  "scenario_id": "2008_GFC"
}
```

#### 4. Output Data Specification

| Field Path | Type | Unit | Description |
|---|---|---|---|
| `scenario_id` | `string` | Key | Unique benchmark scenario code |
| `scenario_name` | `string` | Text | Human-readable crisis title |
| `realized_market_drawdown` | `float` | % | Actual benchmark index drawdown during the historical event |
| `simulated_portfolio_drawdown` | `float` | % | Stressed portfolio loss computed by RiskLattice |
| `cvar_capture_ratio` | `float` | Ratio | Ratio of simulated tail loss to realized market loss ($\ge 0.90$ target) |
| `kupiec_pof.lr_stat` | `float` | $\chi^2$ | Kupiec Likelihood Ratio test statistic |
| `kupiec_pof.p_value` | `float` | Probability | Statistical p-value ($p > 0.05$ indicates model passes coverage test) |
| `kupiec_pof.decision` | `string` | Status | `"ACCEPT_MODEL"` or `"REJECT_MODEL"` |
| `second_order_recall` | `float` | Ratio | Accuracy in discovering indirect counterparty dependencies ($\ge 0.85$ target) |

**Sample Response Payload**:
```json
{
  "scenario_id": "2008_GFC",
  "scenario_name": "2008 Global Financial Crisis / Lehman Collapse",
  "realized_market_drawdown": -0.385,
  "simulated_portfolio_drawdown": -0.362,
  "cvar_capture_ratio": 0.940,
  "kupiec_pof": {
    "lr_stat": 0.482,
    "p_value": 0.487,
    "decision": "ACCEPT_MODEL",
    "total_trials": 504,
    "observed_exceptions": 6,
    "expected_exceptions": 5.04
  },
  "second_order_recall": 0.885
}
```

---

### UC-03: Natural Language Free-Form Scenario Authoring

#### 1. Business Context & Objective
Allows portfolio managers and executives to author arbitrary geopolitical or macroeconomic stress scenarios in plain English without requiring manual entry of factor shock vectors.

#### 2. Primary Endpoints
- `POST /api/v1/scenarios/draft` (Drafts a validated scenario structure)
- `POST /api/v1/stress/simulate` (With `scenario_prompt`)

#### 3. Input Data Specification

| Parameter | Type | Constraints | Req? | Description |
|---|---|---|:---:|---|
| `prompt` / `scenario_prompt` | `string` | 1 - 500 characters | Yes | Plain-English macroeconomic or geopolitical prompt |
| `portfolio_weights` | `object` | Valid ticker weights | Optional | Portfolio holdings to apply shock to |

**Sample Request Payload (`POST /api/v1/stress/simulate`)**:
```json
{
  "scenario_prompt": "Strait of Hormuz is closed due to escalating naval warfare, crude oil jumps 50% and tanker shipping costs double, while sovereign bond yields spike 40 bps."
}
```

#### 4. Output Data Specification
The local LLM translates the semantic intent into clamped factor impulses:
- `CHOKEPOINT_HORMUZ`: `+1.00`
- `BRENT_CRUDE`: `+0.50`
- `BALTIC_DRY`: `+1.00`
- `US10Y_REAL`: `+0.0040`

**Sample Intermediate Translation & Response**:
```json
{
  "translation": {
    "scenario_title": "Hormuz Naval Warfare & Energy Shock",
    "extracted_factors": {
      "BRENT_CRUDE": 0.50,
      "BALTIC_DRY": 1.00,
      "US10Y_REAL": 0.0040
    },
    "affected_sectors": ["Energy", "Marine Shipping", "Utilities", "Aviation"],
    "confidence_score": 0.96
  },
  "simulation": {
    "portfolio_pnl": {
      "total_pnl": -42800000.0,
      "drawdown_pct": -0.095
    }
  }
}
```

---

### UC-04: SEC 10-K Verbatim Dependency Graph Extraction

#### 1. Business Context & Objective
Parses raw SEC Form 10-K Item 1A (Risk Factors) disclosures using an LLM to extract supplier-customer dependency relationships. Rejects any extracted triple if its verbatim quote does not match the source text character-for-character (Zero Hallucination Guardrail).

#### 2. Primary Endpoints
- `POST /api/v1/graph/extract`

#### 3. Input Data Specification

| Parameter | Type | Constraints | Req? | Description |
|---|---|---|:---:|---|
| `chunk_id` | `string` | Valid ID | No | Filing chunk identifier (e.g. `"NVDA_10K_ITEM1A_01"`) |
| `chunk_text` | `string` | Max 10,000 chars | Yes | Raw text extracted from the SEC 10-K filing |
| `company_ticker` | `string` | 1 - 10 chars | Yes | Filing company's ticker symbol |

**Sample Request Payload**:
```json
{
  "chunk_id": "NVDA_10K_ITEM1A_04",
  "company_ticker": "NVDA",
  "chunk_text": "We rely on Taiwan Semiconductor Manufacturing Company Limited (TSMC) to manufacture all of our GPU silicon wafers. In addition, we utilize packaging and testing services from Amkor Technology and ASE Group."
}
```

#### 4. Output Data Specification

| Field Path | Type | Description |
|---|---|---|
| `company_ticker` | `string` | Source company ticker |
| `extracted_edges_count` | `int` | Count of validated relationships |
| `edges[].source_id` | `string` | Supplier / predecessor node ID |
| `edges[].target_id` | `string` | Customer / successor node ID |
| `edges[].relation_type` | `string` | Relationship type (`"SUPPLIER_TO"`, `"PACKAGING_PARTNER"`) |
| `edges[].base_weight` | `float` | Estimated revenue/supply dependency sensitivity ($0.0 - 1.0$) |
| `edges[].evidence_quote` | `string` | Exact verbatim substring verified in source text |
| `edges[].char_offset_start`| `int` | Exact character start position in chunk |
| `edges[].char_offset_end` | `int` | Exact character end position in chunk |

**Sample Response Payload**:
```json
{
  "company_ticker": "NVDA",
  "extracted_edges_count": 2,
  "edges": [
    {
      "source_id": "TSM",
      "target_id": "NVDA",
      "relation_type": "SUPPLIER_TO",
      "base_weight": 0.85,
      "evidence_quote": "We rely on Taiwan Semiconductor Manufacturing Company Limited (TSMC) to manufacture all of our GPU silicon wafers.",
      "char_offset_start": 0,
      "char_offset_end": 115
    },
    {
      "source_id": "AMKR",
      "target_id": "NVDA",
      "relation_type": "PACKAGING_PARTNER",
      "base_weight": 0.35,
      "evidence_quote": "we utilize packaging and testing services from Amkor Technology",
      "char_offset_start": 133,
      "char_offset_end": 196
    }
  ]
}
```

---

### UC-05: Institutional Multi-Asset Portfolio Convexity Valuation

#### 1. Business Context & Objective
Revalues institutional multi-asset portfolios containing non-linear derivatives, corporate bonds, credit default swaps, private credit loans, and structured credit tranches. Evaluates Greeks ($\Delta, \Gamma, \nu, \Theta$), Merton credit spread widening, and covenant breach penalties.

#### 2. Primary Endpoints
- `POST /api/v1/portfolio/ingest`
- `POST /api/v1/portfolios/{portfolio_id}/versions`

#### 3. Input Data Specification (7 Asset Classes)

Each holding specifies instrument-specific financial parameters:
- **`EQUITY`**: `ticker`, `notional`, `weight`, `side` (`LONG`/`SHORT`).
- **`OPTION`**: `option_type` (`CALL`/`PUT`), `strike`, `underlying_price`, `implied_vol`, `maturity_years`.
- **`BOND`**: `duration`, `convexity`, `spread_bps`, `maturity_years`.
- **`CDS`**: `spread_bps`, `recovery_rate` ($R \in [0, 1]$), `maturity_years`.
- **`PRIVATE_CREDIT`**: `covenant_max_leverage`, `current_leverage`, `recovery_rate`.
- **`FX`**: `currency`, `maturity_years`.
- **`CLO`**: `attachment_point`, `detachment_point`, `recovery_rate`.

**Sample Request Payload (`POST /api/v1/portfolios/PORT_CITADEL_01/versions`)**:
```json
{
  "portfolio_version_id": "V2026_11_17_01",
  "portfolio_id": "PORT_CITADEL_01",
  "base_currency": "USD",
  "as_of": "2026-11-17T00:00:00Z",
  "holdings": [
    {
      "node_id": "NVDA",
      "ticker": "NVDA",
      "asset_class": "EQUITY",
      "notional": 50000000.0,
      "weight": 0.25,
      "side": "LONG"
    },
    {
      "node_id": "AMD_PUT_200",
      "ticker": "AMD",
      "asset_class": "OPTION",
      "option_type": "PUT",
      "notional": 10000000.0,
      "weight": 0.05,
      "side": "LONG",
      "strike": 180.0,
      "underlying_price": 200.0,
      "implied_vol": 0.42,
      "maturity_years": 0.25
    },
    {
      "node_id": "FORD_BOND_2029",
      "ticker": "F",
      "asset_class": "BOND",
      "notional": 20000000.0,
      "weight": 0.10,
      "side": "LONG",
      "duration": 4.8,
      "convexity": 28.5,
      "spread_bps": 240.0,
      "maturity_years": 5.0
    },
    {
      "node_id": "INTC_CDS_5Y",
      "ticker": "INTC",
      "asset_class": "CDS",
      "notional": 30000000.0,
      "weight": 0.15,
      "side": "BUY",
      "spread_bps": 125.0,
      "recovery_rate": 0.40,
      "maturity_years": 5.0
    },
    {
      "node_id": "PC_SUPPLY_CHAIN_LENDING",
      "ticker": "APTV",
      "asset_class": "PRIVATE_CREDIT",
      "notional": 25000000.0,
      "weight": 0.125,
      "covenant_max_leverage": 3.75,
      "current_leverage": 4.10,
      "recovery_rate": 0.60
    }
  ],
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

#### 4. Output Data Specification

| Field Path | Type | Unit | Description |
|---|---|---|---|
| `holding_pnl[NVDA]` | `float` | USD | Equity mark-to-market loss ($N \cdot (\beta S + \frac{1}{2}\gamma S^2)$) |
| `holding_pnl[AMD_PUT]` | `float` | USD | Protective put convexity gain ($\Delta \cdot \Delta S + \frac{1}{2}\Gamma (\Delta S)^2 + \nu \Delta \sigma$) |
| `holding_pnl[FORD_BOND]` | `float` | USD | Bond loss from duration and Merton credit spread widening |
| `holding_pnl[INTC_CDS]` | `float` | USD | Mark-to-market gain on purchased CDS protection |
| `holding_pnl[PC_LENDING]` | `float` | USD | Private credit loan write-down (covenant haircut of 35%) |
| `portfolio_net_pnl` | `float` | USD | Aggregate stressed dollar PnL |

---

### UC-06: Capital-Constrained Tail-Risk Hedge Optimizer

#### 1. Business Context & Objective
Formulates a Mixed-Integer Programming (MILP/MIQP) problem to find the optimal tail-risk hedging basket that minimizes portfolio 99% CVaR under an explicit CapEx budget constraint.

#### 2. Primary Endpoints
- `POST /api/v1/optimize/hedge`

#### 3. Input Data Specification

| Parameter | Type | Unit | Constraints | Req? | Description |
|---|---|---|---|:---:|---|
| `portfolio_notional` | `float` | USD | $> 0$ | Yes | Total portfolio dollar notional |
| `unhedged_pnl` | `float` | USD | $\le 0$ | Yes | Baseline stressed loss without hedges |
| `node_shocks` | `object` | Fraction | Map of node shocks | Yes | Active post-contagion shock vector |
| `budget_limit` | `float` | USD | $> 0$ | Yes | Maximum permissible hedge premium spend |
| `target_drawdown_pct`| `float` | Fraction | $0.0 - 1.0$ | No | Optional drawdown ceiling |

**Sample Request Payload**:
```json
{
  "portfolio_notional": 100000000.0,
  "unhedged_pnl": -22400000.0,
  "node_shocks": {
    "TSM": -0.70,
    "NVDA": -0.535,
    "AAPL": -0.321,
    "F": -0.231
  },
  "budget_limit": 750000.0,
  "target_drawdown_pct": 0.12
}
```

#### 4. Output Data Specification

| Field Path | Type | Unit | Description |
|---|---|---|---|
| `initial_pnl` | `float` | USD | Baseline stressed portfolio loss |
| `hedged_pnl` | `float` | USD | Net portfolio loss after hedge payoff |
| `pnl_improvement` | `float` | USD | Dollar protection achieved |
| `total_hedge_cost` | `float` | USD | Total premium spent (must be $\le \text{budget\_limit}$) |
| `cvar_reduction_pct` | `float` | % | Downside tail risk reduction percentage |
| `recommendations[]` | `array` | Objects | Exact contract allocations (`instrument_name`, `target_node`, `allocated_notional`, `estimated_cost`, `pnl_protection`) |
| `efficient_frontier[]`| `array` | Objects | Efficient frontier curve points (`cost`, `pnl_reduction`, `cvar_reduction_pct`) |

**Sample Response Payload**:
```json
{
  "initial_pnl": -22400000.0,
  "hedged_pnl": -12150000.0,
  "pnl_improvement": 10250000.0,
  "total_hedge_cost": 680000.0,
  "initial_cvar_99": 28500000.0,
  "hedged_cvar_99": 16200000.0,
  "cvar_reduction_pct": 43.16,
  "recommendations": [
    {
      "candidate_id": "SOXX_PUT_15OTM",
      "instrument_name": "SOXX 3M 15% OTM Put",
      "target_node": "NVDA",
      "action": "BUY",
      "allocated_notional": 15000000.0,
      "estimated_cost": 420000.0,
      "pnl_protection": 6800000.0,
      "description": "Hedges downstream semiconductor OEM exposure"
    },
    {
      "candidate_id": "HYG_PUT_5OTM",
      "instrument_name": "HYG High-Yield Put",
      "target_node": "F",
      "action": "BUY",
      "allocated_notional": 8000000.0,
      "estimated_cost": 260000.0,
      "pnl_protection": 3450000.0,
      "description": "Hedges automotive corporate credit spread blowout"
    }
  ]
}
```

---

### UC-07: Algorithmic Reverse Stress Testing

#### 1. Business Context & Objective
Inverts the stress simulation to identify the **minimal-norm systemic shock vector** $\mathbf{s}^*$ that forces the portfolio past a designated catastrophic loss threshold (e.g., $-20\%$), uncovering hidden structural failure paths.

#### 2. Primary Endpoints
- `POST /api/v1/stress/reverse`

#### 3. Input Data Specification

| Parameter | Type | Unit | Range | Req? | Description |
|---|---|---|---|:---:|---|
| `portfolio_notional` | `float` | USD | $> 0$ | Yes | Portfolio dollar size |
| `target_loss_pct` | `float` | Fraction | $0.05 - 0.90$ | Yes | Target drawdown threshold (e.g. $0.20 = 20\%$) |
| `factor_sensitivities`| `object` | Sensitivities | Factor IDs $\to$ Floats | No | Optional custom asset-to-factor elasticities |

**Sample Request Payload**:
```json
{
  "portfolio_notional": 100000000.0,
  "target_loss_pct": 0.20
}
```

#### 4. Output Data Specification

| Field Path | Type | Unit | Description |
|---|---|---|---|
| `target_loss_pct` | `float` | % | Requested breach threshold |
| `achieved_loss_pct` | `float` | % | Drawdown achieved by the minimal shock vector |
| `minimal_shocks` | `object` | Fraction | Minimal factor shock vector $\mathbf{s}^*$ |
| `norm_l2` | `float` | Norm | Euclidean norm $\|\mathbf{s}^*\|_2$ (smaller = more vulnerable) |
| `critical_factor` | `string` | ID | Factor that drives the earliest breach |
| `top_vulnerable_nodes`| `array[string]`| Tickers | Portfolio assets most sensitive to the minimal shock |
| `iterations` | `int` | Count | Inverse solver convergence iterations |

**Sample Response Payload**:
```json
{
  "target_loss_pct": 0.20,
  "achieved_loss_pct": 0.2014,
  "minimal_shocks": {
    "FOUNDRY_TW": -0.184,
    "SOFR_SPREAD": 0.0125,
    "BALTIC_DRY": 0.420
  },
  "norm_l2": 0.4612,
  "critical_factor": "FOUNDRY_TW",
  "top_vulnerable_nodes": ["NVDA", "TSM", "F", "AAPL"],
  "iterations": 14
}
```

---

### UC-08: Multi-Period Forward Timeline Simulation (0-90 Days)

#### 1. Business Context & Objective
Simulates dynamic multi-period wave propagation across a forward horizon $T \in [0, 90]$ days, tracking days-of-inventory ($\text{DOI}$) buffer exhaustion and milestone cascades.

#### 2. Primary Endpoints
- `POST /api/v1/stress/timeline`

#### 3. Input Data Specification

| Parameter | Type | Unit | Description |
|---|---|---|---|
| `initial_shocks` | `object` | Fraction | Initial factor/node impulses |
| `portfolio_notional` | `float` | USD | Total portfolio value |
| `time_horizon_days` | `array[int]` | Days | Evaluation milestone days (defaults to `[0, 7, 14, 30, 60, 90]`) |
| `inventory_days` | `object` | Days | Custom safety stock buffer days per node |

**Sample Request Payload**:
```json
{
  "initial_shocks": {
    "FOUNDRY_TW": -0.65,
    "BALTIC_DRY": 1.40
  },
  "portfolio_notional": 100000000.0,
  "time_horizon_days": [0, 7, 14, 30, 45, 60, 90],
  "inventory_days": {
    "NVDA": 45,
    "AAPL": 60,
    "F": 14
  }
}
```

#### 4. Output Data Specification

| Field Path | Type | Unit | Description |
|---|---|---|---|
| `peak_drawdown_pnl` | `float` | USD | Maximum cumulative dollar loss across the timeline |
| `peak_drawdown_day` | `int` | Day | Day index where peak loss occurs |
| `steps[].day` | `int` | Day | Simulation step day |
| `steps[].cumulative_pnl`| `float` | USD | Stressed portfolio loss at day $t$ |
| `steps[].inventory_levels`| `object` | Days | Remaining physical buffer days per node |
| `steps[].milestones[]` | `array` | Objects | Triggered events (`day`, `event_type`, `node_id`, `severity`, `description`) |

**Sample Response Payload**:
```json
{
  "initial_pnl": 0.0,
  "peak_drawdown_pnl": -21850000.0,
  "peak_drawdown_day": 60,
  "peak_drawdown_pct": -0.2185,
  "total_milestones": 3,
  "steps": [
    {
      "day": 14,
      "cumulative_pnl": -4200000.0,
      "inventory_levels": { "NVDA": 31, "AAPL": 46, "F": 0 },
      "milestones": [
        {
          "day": 14,
          "event_type": "INVENTORY_EXHAUSTED",
          "node_id": "F",
          "severity": "CRITICAL",
          "description": "Ford safety stock depleted; assembly line disruption begins."
        }
      ]
    },
    {
      "day": 45,
      "cumulative_pnl": -18400000.0,
      "inventory_levels": { "NVDA": 0, "AAPL": 15, "F": 0 },
      "milestones": [
        {
          "day": 45,
          "event_type": "INVENTORY_EXHAUSTED",
          "node_id": "NVDA",
          "severity": "CRITICAL",
          "description": "Nvidia wafer buffer exhausted; GPU supply cuts hit cloud providers."
        }
      ]
    }
  ]
}
```

---

### UC-09: Scenario Diffing & Shapley/Euler Attribution

#### 1. Business Context & Objective
Performs side-by-side comparative risk attribution between a baseline scenario and a stressed/hedged scenario, calculating marginal factor contributions and node-by-node risk shifts.

#### 2. Primary Endpoints
- `POST /api/v1/scenario/diff`

#### 3. Input Data Specification

| Parameter | Type | Unit | Description |
|---|---|---|---|
| `scenario_a_name` | `string` | Text | Baseline scenario label |
| `scenario_b_name` | `string` | Text | Alternate scenario label |
| `shocks_a` | `object` | Fraction | Factor shock vector for Scenario A |
| `shocks_b` | `object` | Fraction | Factor shock vector for Scenario B |
| `positions` | `object` | USD | Dollar position sizes per holding |

**Sample Request Payload**:
```json
{
  "scenario_a_name": "Unhedged Foundry Halt",
  "scenario_b_name": "Hedged with SOXX Puts & Dual-Sourcing",
  "shocks_a": { "FOUNDRY_TW": -0.70, "BALTIC_DRY": 1.80 },
  "shocks_b": { "FOUNDRY_TW": -0.35, "BALTIC_DRY": 0.90 },
  "positions": { "NVDA": 25000000.0, "TSM": 20000000.0, "AAPL": 20000000.0, "F": 10000000.0 }
}
```

#### 4. Output Data Specification

| Field Path | Type | Unit | Description |
|---|---|---|---|
| `pnl_a` / `pnl_b` | `float` | USD | Portfolio loss for Scenario A and Scenario B |
| `delta_pnl` | `float` | USD | Net PnL difference ($B - A$) |
| `delta_cvar_99` | `float` | USD | Tail risk reduction |
| `net_improvement_pct` | `float` | % | Percentage risk reduction |
| `node_diffs[]` | `array` | Objects | Holding-level breakdown (`node_id`, `shock_a`, `shock_b`, `delta_pnl`, `status`) |
| `top_de_risked_nodes` | `array` | Objects | Holdings with the largest risk reduction |

---

### UC-10: Endogenous Liquidity, Almgren-Chriss Slippage & Margin Spirals

#### 1. Business Context & Objective
Models the execution slippage of liquidating large portfolio positions during a crisis using the **Almgren-Chriss (2000)** optimal execution model, coupled with fire-sale contagion multipliers ($\xi$) and ISDA SIMM 99% margin calls.

#### 2. Primary Endpoints
- `POST /api/v1/liquidity/simulate`

#### 3. Input Data Specification

| Parameter | Type | Unit | Range | Req? | Description |
|---|---|---|---|:---:|---|
| `positions[]` | `array` | Objects | List of asset positions | Yes | Holdings with ADV, volatility, and bid-ask spread |
| `liquidation_pct` | `float` | Fraction | $0.05 - 1.00$ | Yes | Fraction of portfolio notional liquidated |
| `participation_rate`| `float` | Fraction | $0.01 - 0.30$ | Yes | Maximum daily volume participation rate |
| `fund_unencumbered_cash`| `float` | USD | $\ge 0$ | Yes | Cash buffer available to meet margin calls |
| `portfolio_unhedged_pnl`| `float` | USD | $\le 0$ | Yes | Unrealized derivative MTM losses |
| `gross_derivative_notional`| `float` | USD | $\ge 0$ | Yes | Gross notional of derivative contracts |

**Sample Request Payload**:
```json
{
  "liquidation_pct": 0.20,
  "participation_rate": 0.10,
  "fund_unencumbered_cash": 15000000.0,
  "portfolio_unhedged_pnl": -23450000.0,
  "gross_derivative_notional": 50000000.0,
  "positions": [
    {
      "asset_id": "NVDA",
      "target_notional": 25000000.0,
      "adv_30d": 120000000.0,
      "volatility_ann": 0.45,
      "bid_ask_spread_bps": 3.5,
      "liquidation_urgency": "HIGH"
    },
    {
      "asset_id": "F",
      "target_notional": 10000000.0,
      "adv_30d": 35000000.0,
      "volatility_ann": 0.35,
      "bid_ask_spread_bps": 5.0,
      "liquidation_urgency": "FIRE_SALE"
    }
  ]
}
```

#### 4. Output Data Specification

| Field Path | Type | Unit | Description |
|---|---|---|---|
| `total_notional_liquidated` | `float` | USD | Dollar notional sold |
| `total_market_impact_loss` | `float` | USD | Total execution slippage ($I_{\text{temp}} + I_{\text{perm}}$) |
| `blended_price_discount_pct`| `float` | % | Average realized price concession |
| `fire_sale_contagion_multiplier`| `float` | Multiplier | Fire-sale liquidity amplification $\xi \in [1.0, 3.5]$ |
| `margin_summary.isda_simm_call` | `float` | USD | Required 10-day 99% initial margin call |
| `margin_summary.post_stress_lcr`| `float` | Ratio | Post-liquidation Liquidity Coverage Ratio ($>1.0$ = compliant) |
| `asset_impacts[]` | `array` | Objects | Breakdown per asset (`temp_impact_loss`, `perm_impact_loss`, `days_to_liquidate`) |

**Sample Response Payload**:
```json
{
  "total_notional_liquidated": 7000000.0,
  "total_market_impact_loss": 582450.0,
  "blended_price_discount_pct": 8.32,
  "fire_sale_contagion_multiplier": 1.45,
  "margin_summary": {
    "isda_simm_call": 4850000.0,
    "variation_margin_drain": 23450000.0,
    "total_liquidity_drain": 28882450.0,
    "post_stress_lcr": 0.52,
    "lcr_status": "DEFICIT"
  }
}
```

---

### UC-11: What-If Supply Chain Graph Mutation Studio

#### 1. Business Context & Objective
Simulates proactive topological interventions in the corporate supply network—such as severing single-source dependencies or qualifying secondary dual-sourcing foundries—and quantifies **Resilience ROI** ($\Delta\text{PnL} / \text{CapEx}$).

#### 2. Primary Endpoints
- `POST /api/v1/mutation/evaluate`

#### 3. Input Data Specification

| Parameter | Type | Unit | Description |
|---|---|---|---|
| `mutation_name` | `string` | Text | Intervention strategy title |
| `mutations[]` | `array[object]` | Actions | List of topological modifications |
| `mutations[].mutation_type` | `string` | Enum | `"SEVER_EDGE"`, `"ADD_EDGE"`, `"REWEIGHT_EDGE"` |
| `mutations[].source_id` | `string` | Node ID | Predecessor supplier node |
| `mutations[].target_id` | `string` | Node ID | Successor customer node |
| `mutations[].new_weight` | `float` | Fraction | New dependency weight |
| `mutations[].capex_cost` | `float` | USD | Capital expenditure required to execute mutation |
| `mutations[].lead_time_months`| `int` | Months | Implementation timeline |

**Sample Request Payload**:
```json
{
  "mutation_name": "TSMC Fab 21 & Intel Dual-Sourcing",
  "mutations": [
    {
      "mutation_type": "REWEIGHT_EDGE",
      "source_id": "TSM",
      "target_id": "NVDA",
      "new_weight": 0.15,
      "capex_cost": 2500000.0,
      "lead_time_months": 12,
      "rationale": "Shift 60% packaging to TSMC Phoenix, Arizona"
    },
    {
      "mutation_type": "ADD_EDGE",
      "source_id": "INTC",
      "target_id": "NVDA",
      "new_weight": 0.20,
      "capex_cost": 1200000.0,
      "lead_time_months": 8,
      "rationale": "Qualify Intel Foundry Services for secondary wafer sourcing"
    }
  ]
}
```

#### 4. Output Data Specification

| Field Path | Type | Unit | Description |
|---|---|---|---|
| `base_pnl` | `float` | USD | Stressed loss under baseline graph |
| `mutated_pnl` | `float` | USD | Stressed loss under re-engineered graph |
| `pnl_savings` | `float` | USD | Dollar damage avoided ($\Delta\text{PnL}$) |
| `total_capex` | `float` | USD | Total capital cost of modifications |
| `resilience_roi` | `float` | Ratio | $\Delta\text{PnL} / \text{CapEx}$ ($>1.0$ indicates positive financial return) |
| `regulatory_capital_relief` | `float` | USD | Estimated Pillar 2 capital charge reduction |

**Sample Response Payload**:
```json
{
  "mutation_name": "TSMC Fab 21 & Intel Dual-Sourcing",
  "base_pnl": -28500000.0,
  "mutated_pnl": -16200000.0,
  "pnl_savings": 12300000.0,
  "total_capex": 3700000.0,
  "resilience_roi": 3.32,
  "regulatory_capital_relief": 4850000.0
}
```

---

### UC-12: Live Satellite AIS Maritime Telemetry & Threat Ingestion

#### 1. Business Context & Objective
Ingests real-time Automatic Identification System (AIS) transponder data and military threat wires across 5 maritime choke points, updating the composite **Systemic Vulnerability Index (SVI $0-100$)** and feeding live decaying impulses into the contagion matrix.

#### 2. Primary Endpoints
- `GET /api/v1/threats/ais/status` (Current radar snapshot)
- `POST /api/v1/threats/ais/tick` (Advances discrete traffic drift)
- `POST /api/v1/threats/ingest` (Ingests breaking threat headline)
- `POST /api/v1/threats/inject` (Injects threat into active simulation)
- `GET /api/v1/threats/stream` (SSE live stream of transponder updates)

#### 3. Input Data Specification (`POST /api/v1/threats/ingest`)

| Parameter | Type | Unit | Description |
|---|---|---|---|
| `headline` | `string` | Text | Breaking intelligence wire headline |
| `source` | `string` | Text | News / sensor source (e.g. `"Reuters"`, `"Lloyd's List"`) |
| `severity` | `string` | Enum | `"CRITICAL"`, `"HIGH"`, `"MEDIUM"`, `"LOW"` |
| `choke_point_id` | `string` | ID | `"GEO_TAIWAN_STRAIT"`, `"GEO_MALACCA"`, `"GEO_SUEZ"`, etc. |
| `affected_nodes` | `array[string]`| Node IDs | Nodes directly disrupted by the event |
| `raw_supply_impact_pct`| `float` | Fraction | Direct supply reduction ($[-0.95, 0.0]$) |

**Sample Request Payload (`POST /api/v1/threats/ingest`)**:
```json
{
  "headline": "Taiwan Strait: Live-Fire Naval Drills Block Commercial Shipping Lanes",
  "source": "Lloyd's Maritime Intelligence",
  "severity": "CRITICAL",
  "choke_point_id": "GEO_TAIWAN_STRAIT",
  "affected_nodes": ["TSM", "2317_TW", "ZIM"],
  "raw_supply_impact_pct": -0.65,
  "details": "Container carriers rerouting around eastern Taiwan; transit delays estimated at 8-12 days."
}
```

#### 4. Output Data Specification (`GET /api/v1/threats/ais/status`)

| Field Path | Type | Unit | Description |
|---|---|---|---|
| `svi_index` | `float` | Index | Systemic Vulnerability Index ($0.0 - 100.0$) |
| `svi_status` | `string` | Status | `"NORMAL"`, `"ELEVATED"`, `"SEVERE"`, `"CRITICAL"` |
| `choke_points[].congestion_index`| `float` | Ratio | Vessel congestion ratio $C \ge 1.0$ |
| `choke_points[].demurrage_surge_pct`| `float` | % | Charter rate demurrage surge |
| `choke_points[].disruption_prob`| `float` | Probability | Probability of sustained commercial traffic stoppage |
| `recent_threats[]` | `array` | Objects | Active threat events with decaying impulse values |

**Sample Response Payload**:
```json
{
  "svi_index": 76.4,
  "svi_status": "CRITICAL",
  "active_threats_count": 3,
  "choke_points": [
    {
      "choke_point_id": "GEO_TAIWAN_STRAIT",
      "name": "Taiwan Strait Maritime Corridor",
      "active_vessels": 234,
      "median_speed_knots": 4.2,
      "congestion_index": 2.23,
      "demurrage_surge_pct": 178.5,
      "disruption_prob": 0.88,
      "status": "CRITICAL"
    }
  ]
}
```

---

### UC-13: Autonomous SEC EDGAR Continuous Crawler

#### 1. Business Context & Objective
Polls and ingests SEC Form 10-K, 10-Q, and 8-K filings from the SEC EDGAR system, parsing material supply chain disclosures and updating edge weights in the DuckDB graph.

#### 2. Primary Endpoints
- `GET /api/v1/edgar/status`
- `POST /api/v1/edgar/ingest`

#### 3. Input Data Specification (`POST /api/v1/edgar/ingest`)

| Parameter | Type | Description |
|---|---|---|
| `ticker` | `string` | Filing company stock symbol |
| `filing_type` | `string` | `"10-K"`, `"10-Q"`, `"8-K"` |
| `accession_number` | `string` | Official SEC accession number (e.g. `0001045810-24-000029`) |
| `filing_text` | `string` | Unstructured disclosure text |

#### 4. Output Data Specification
Returns discovered counterparty edges with confidence scores and verbatim quotes:
```json
{
  "ticker": "AAPL",
  "discovered_edges": [
    {
      "source_id": "TSM",
      "target_id": "AAPL",
      "relation_type": "SUPPLIER_TO",
      "confidence": 0.98,
      "quote": "TSMC manufactures custom silicon applications including our A-series and M-series chips."
    }
  ]
}
```

---

### UC-14: Interactive Geospatial Physical Lattice

#### 1. Business Context & Objective
Returns global geospatial coordinates (WGS84) for mega-fabs, assembly complexes, container ports, and maritime choke points to render interactive physical transit overlays in Cytoscape.js and OpenLayers/Mapbox.

#### 2. Primary Endpoints
- `GET /api/v1/graph/geospatial`

#### 3. Output Data Specification

```json
{
  "facilities": [
    {
      "id": "TSMC_FAB18",
      "ticker": "TSM",
      "name": "TSMC Fab 18 (3nm/5nm GigaFab)",
      "lat": 23.116,
      "lng": 120.278,
      "city": "Tainan",
      "country": "Taiwan",
      "type": "FAB",
      "criticality": 1.0
    }
  ],
  "corridors": [
    {
      "from": "TSMC_FAB18",
      "to": "FOXCONN_ZHENGZHOU",
      "mode": "AIR_FREIGHT",
      "dependency": 0.85
    }
  ]
}
```

---

### UC-15: PMS/OMS Ingestion & Fed CCAR Form FR Y-14A Export

#### 1. Business Context & Objective
Ingests institutional trade blotters from BlackRock Aladdin or Bloomberg PORT, normalizes them into RiskLattice's 7 asset classes, and exports regulatory stress test submission packets matching Federal Reserve Form FR Y-14A Schedule A.

#### 2. Primary Endpoints
- `POST /api/v1/pms/aladdin/import`
- `POST /api/v1/regulatory/ccar/export`

#### 3. Input Data Specification (`POST /api/v1/pms/aladdin/import`)

Accepts multi-column CSV string with headers: `Ticker,AssetClass,Notional,Side,Duration,Strike,Expiry`.

**Sample Request Payload**:
```json
{
  "csv_content": "Ticker,AssetClass,Notional,Side,Duration,Strike,Expiry\nNVDA,EQUITY,25000000,LONG,,,\nTSM,EQUITY,20000000,LONG,,,\nF,BOND,10000000,LONG,4.8,,\nAMD,OPTION,5000000,LONG,,180,2026-12-18"
}
```

#### 4. Output Data Specification (`POST /api/v1/regulatory/ccar/export`)
Produces a structured Federal Reserve Form FR Y-14A Schedule A packet:
```json
{
  "schedule": "Form FR Y-14A Schedule A - Trading & Counterparty MTM",
  "as_of_date": "2026-11-17",
  "institution_name": "Citadel Global Equities & Quantitative Strategies",
  "supervisory_scenario": "Severely Adverse - Global Semiconductor Blockade",
  "summary_metrics": {
    "total_trading_assets": 100000000.0,
    "projected_mtm_loss": -23450000.0,
    "stressed_cvar_99": 29312500.0,
    "stressed_var_95": 21200000.0,
    "tier1_capital_depletion_pct": 2.34
  }
}
```

---

### UC-16: Conversational AI Chief Risk Officer Copilot

#### 1. Business Context & Objective
Provides an interactive AI conversational agent that answers complex questions from board members and risk managers regarding active simulation results, inventory buffers, and 10-K citations.

#### 2. Primary Endpoints
- `POST /api/v1/copilot/chat`

#### 3. Input Data Specification

| Parameter | Type | Description |
|---|---|---|
| `query` | `string` | User's question in natural language |
| `portfolio_notional` | `float` | Current portfolio size |
| `unhedged_pnl` | `float` | Current stressed loss |
| `node_shocks` | `object` | Active node shock map |

**Sample Request Payload**:
```json
{
  "query": "Why is Ford losing so much money when TSMC is the only company with direct news?",
  "portfolio_notional": 100000000.0,
  "unhedged_pnl": -22400000.0,
  "node_shocks": { "TSM": -0.70, "F": -0.231 }
}
```

#### 4. Output Data Specification
```json
{
  "query": "Why is Ford losing so much money when TSMC is the only company with direct news?",
  "intent": "TRANSMISSION_EXPLANATION",
  "answer": "Ford experiences second-order contagion because its tier-1 suppliers (NXP Semiconductors and Aptiv) rely on TSMC for automotive microcontrollers [10-K Chunk #14]. Furthermore, Ford's high leverage (NetDebt/EBITDA of 4.8) triggers a distress multiplier of lambda=1.63x, amplifying its loss from -14.2% to -23.1%.",
  "cited_nodes": ["TSM", "F", "NXPI", "APTV"],
  "citations": [
    {
      "source": "SEC Form 10-K Item 1A",
      "quote": "Our automotive manufacturing operations depend on single-source microcontrollers manufactured in Taiwan."
    }
  ]
}
```

---

### UC-17: Multi-Channel Webhook Alerting & Incident Dispatch

#### 1. Business Context & Objective
Monitors real-time stress runs against institutional risk appetite limits and dispatches formatted alerts to Slack (Block Kit), Microsoft Teams (Adaptive Cards), and PagerDuty.

#### 2. Primary Endpoints
- `GET /api/v1/alerts`
- `POST /api/v1/alerts/test`

#### 3. Input Data Specification (`POST /api/v1/alerts/test`)

| Parameter | Type | Unit | Description |
|---|---|---|---|
| `scenario_name` | `string` | Text | Evaluated scenario name |
| `portfolio_notional`| `float` | USD | Total portfolio value |
| `pnl_loss` | `float` | USD | Computed stress loss |
| `cvar_99` | `float` | USD | 99% Expected Shortfall |
| `limit_drawdown_pct`| `float` | % | Institutional limit threshold (e.g. $-15.0\%$) |

#### 4. Output Data Specification
Returns dispatched alert and formatted Slack Block Kit JSON:
```json
{
  "alert": {
    "alert_id": "ALT-884920",
    "severity": "CRITICAL",
    "title": "RISK LIMIT BREACH: Portfolio Drawdown -23.45% Exceeds -15.0% Appetite",
    "status": "DISPATCHED"
  },
  "slack_payload": {
    "blocks": [
      {
        "type": "header",
        "text": { "type": "plain_text", "text": "🚨 RiskLattice Alert: Limit Breach" }
      },
      {
        "type": "section",
        "fields": [
          { "type": "mrkdwn", "text": "*Scenario:* Taiwan Strait Naval Quarantine" },
          { "type": "mrkdwn", "text": "*Stressed Drawdown:* -$23,450,000 (-23.45%)" },
          { "type": "mrkdwn", "text": "*99% CVaR:* $29,312,500" },
          { "type": "mrkdwn", "text": "*Status:* IMMEDIATE ACTION REQUIRED" }
        ]
      }
    ]
  }
}
```

---

### UC-18: Executive Memo Generator & Four-Eyes Cryptographic Audit

#### 1. Business Context & Objective
Compiles board-ready C-suite risk memos and enforces a **Four-Eyes dual-key cryptographic governance sign-off** workflow (Draft $\to$ Under Review $\to$ Approved $\to$ Locked) satisfying Federal Reserve SR 11-7 model governance rules.

#### 2. Primary Endpoints
- `POST /api/v1/report/executive`
- `POST /api/v1/audit/submit`
- `POST /api/v1/audit/approve`
- `POST /api/v1/audit/lock`

#### 3. Input Data Specification (`POST /api/v1/report/executive`)

| Parameter | Type | Description |
|---|---|---|
| `scenario_name` | `string` | Scenario title |
| `portfolio_notional`| `float` | Portfolio dollar size |
| `pnl_loss` | `float` | Stressed dollar loss |
| `cvar_99` | `float` | 99% Expected Shortfall |
| `var_95` | `float` | 95% Value at Risk |
| `cro_name` | `string` | Name of signing Chief Risk Officer |
| `firm_name` | `string` | Financial institution name |

#### 4. Output Data Specification
Returns structured JSON memo metadata, HTML template, and SHA-256 digital seal:
```json
{
  "memo_id": "MEMO-20261117-001",
  "scenario_name": "Taiwan Strait Blockade & Semiconductor Shock",
  "pnl_impact": -23450000.0,
  "cvar_99": 29312500.0,
  "html_url": "/api/v1/report/executive/MEMO-20261117-001/html",
  "audit_entry": {
    "run_id": "RUN-20261117-01",
    "status": "APPROVED",
    "primary_signature": "sarah.chen@citadel.com",
    "secondary_signature": "marcus.vance@citadel.com",
    "sha256_seal": "8f4e2b1c9a6d3e7f0b5a8c2d4e6f1a9b3c5e7d9a1f2b4c6e8d0a2c4e6f8b0d2e"
  }
}
```

---

### UC-19: Google Workspace Enterprise SSO & 4-Tier RBAC

#### 1. Business Context & Objective
Authenticates users via Google OAuth2 / OpenID Connect, verifies cryptographic JWT signatures, and maps users to 4 institutional roles:
- `CRO` (Full administrative, simulation, and sign-off authority)
- `PORTFOLIO_MANAGER` (Simulation, what-if mutation, and hedge optimization)
- `RISK_ANALYST` (Simulation and draft submission)
- `AUDITOR` (Read-only access to audit vault, run manifests, and model validation logs)

#### 2. Primary Endpoints
- `POST /api/v1/auth/google`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`

#### 3. Input Data Specification (`POST /api/v1/auth/google`)

| Parameter | Type | Description |
|---|---|---|
| `id_token` | `string` | Google OAuth2 JWT identity token |
| `persona` | `string` | Optional sandbox persona (`"cro"`, `"pm"`, `"analyst"`, `"auditor"`) |

**Sample Request Payload**:
```json
{
  "persona": "cro"
}
```

#### 4. Output Data Specification (`GET /api/v1/auth/me`)

```json
{
  "user_id": "USR-884920",
  "email": "sarah.chen@citadel.com",
  "name": "Sarah Chen, Ph.D.",
  "role": "CHIEF_RISK_OFFICER",
  "organization": "Citadel Global Equities",
  "permissions": [
    "SIMULATE_STRESS",
    "OPTIMIZE_HEDGES",
    "EVALUATE_MUTATIONS",
    "SUBMIT_AUDIT",
    "APPROVE_AUDIT",
    "LOCK_VAULT",
    "EXPORT_CCAR",
    "DISPATCH_ALERTS"
  ]
}
```

---

## Data Verification & Invariant Boundary Checklist

Every input and output across all 19 use cases adheres to the following computational and regulatory invariants:

1. **Energy Conservation & Contagion Damping**: At every propagation hop $k$, the transmitted shock is strictly bounded:
   $$\|\Delta \mathbf{s}^{(k)}\|_\infty \le \alpha^k \cdot \|\mathbf{s}^{(0)}\|_\infty, \quad \alpha = 0.65$$
2. **Numerical Clamping Bounds**: Node shocks are strictly clamped to $[-0.95, +1.50]$ to prevent negative prices or infinite economic cascades.
3. **Local Privacy Firewall (Rule P-01)**: Raw dollar balances, share quantities, and account IDs are stripped before prompts touch LLM components.
4. **AST Pure Compute Isolation (ADR-002)**: The quantitative engine in `backend/app/engine/*.py` contains zero network or database dependencies (`httpx`, `duckdb`, `fastapi`).
5. **Kupiec POF Statistical Adequacy**: All crisis backtests must maintain empirical $p > 0.05$ under the Kupiec $\chi_1^2$ likelihood ratio test.
6. **Dual-Key Cryptographic Governance**: No stress report may be marked `APPROVED` without independent, non-identical primary and secondary signatures.
