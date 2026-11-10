# ContagionGraph: Cross-Asset Macro Contagion Stress-Tester

A hybrid neuro-symbolic financial risk platform combining local-first LLM semantic extraction with a deterministic multi-hop graph propagation and Monte Carlo tail-risk engine.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0-emerald.svg)](https://fastapi.tiangolo.com/)
[![DuckDB](https://img.shields.io/badge/DuckDB-OLAP-amber.svg)](https://duckdb.org/)

---

## 1. System Architecture

ContagionGraph operates on a **strict neuro-symbolic division of labor**:
- **Deterministic Python Math Engine**: All quantitative risk metrics, Huber robust regressions, 4-hop damped message-passing, balance-sheet distress amplifiers ($\lambda_v$), and 10,000-path Student-$t$ Copula CVaR calculations are executed exclusively by NumPy, SciPy, and DuckDB. Zero LLM involvement in numeric computation.
- **Probabilistic Semantic AI (LiteLLM)**: Confined strictly to parsing unstructured SEC Form 10-K filings into typed triples, translating natural-language user scenario prompts into initial impulse vectors $s^{(0)}$, and generating post-mortem narrative explanations with regex-verified citations.
- **Privacy Boundary**: Dollar balances, share quantities, and account IDs remain inside Tier 1 & Tier 2 (DuckDB). External LLMs receive only ticker symbols, public filing text, and normalized unit-free graph paths.

```
┌─────────────────────────────────┐      ┌───────────────────────────────────┐      ┌─────────────────────────────────┐
│     Client Tier (Next.js 15)    │      │    Server Tier (FastAPI + Math)   │      │    LLM Tier (Local or Cloud)    │
│  - Cytoscape.js Network Canvas  │ ───► │  - Huber Robust Regression (W)    │ ───► │  - LiteLLM Router               │
│  - Shock Studio & Factor Sliders│ ◄─── │  - 4-Hop Damped Contagion Engine  │ ◄─── │  - SEC 10-K Verbatim Extractor  │
│  - 1st/2nd/3rd PnL Waterfall    │ (SSE)│  - 10,000 Student-t Copula CVaR   │      │  - Semantic Shock Translator    │
│  - 4 Crisis Replay Backtester   │      │  - Embedded DuckDB 2.0 Store      │      │  - Local PII Sanitizer          │
└─────────────────────────────────┘      └───────────────────────────────────┘      └─────────────────────────────────┘
```

---

## 2. Mathematical Propagation Formulas

Given directed dependency graph $G = (V, E, W)$ with $N = 50$ canonical nodes and adjacency sensitivity matrix $W \in \mathbb{R}^{N \times N}$, and initial impulse vector $s^{(0)} \in [-0.95, +2.00]^N$:

### Hop Iteration ($k = 1, 2, 3, 4$)
$$\Delta s_v^{(k)} = \alpha^{k-1} \sum_u W_{uv} \cdot \Delta s_u^{(k-1)} \cdot (1 - \sigma_v) \cdot \lambda_v$$

- **Hop Decay Factor**: $\alpha = 0.65$
- **Supplier Substitutability**: $\sigma_v \in [0.0, 0.8]$
- **Non-Linear Distress Multiplier**:
  $$\lambda_v = \begin{cases} 1 + 0.35 \cdot \max(0, \text{NetDebt/EBITDA} - 3.0), & \text{if } \text{NetDebt/EBITDA} > 3.0 \text{ or } \text{InterestCoverage} < 1.5 \text{ and } \Delta s < 0 \\ 1.0, & \text{otherwise} \end{cases}$$
- **Cumulative Clamped Node Shock**:
  $$S_v = \text{clip}\left(\sum_{k=0}^4 \Delta s_v^{(k)}, -0.95, +1.50\right)$$
  Decomposed into 1st-order (direct macro), 2nd-order (tier-1 supplier), and 3rd/4th-order (network contagion) contributions.

---

## 3. Four Historical Crisis Replay Benchmarks

| Crisis Regime | Primary Impulse Vector $s^{(0)}$ | Expected Multi-Hop Path | Target Benchmark Metric |
| :--- | :--- | :--- | :--- |
| **1. 2008 Liquidity & Credit Freeze** | `HY_OAS: +8.5%`, `SOFR_SPREAD: +3.5%` | Interbank freeze $\to$ regional bank warehouse lines $\to$ high-leverage REITs & auto-loan securitizers | Contagion CVaR captures $\ge 90\%$ realized drawdown vs $<55\%$ for 60d Gaussian VaR |
| **2. 2020 Mobility & Supply Halt** | `BRENT_CRUDE: -55%`, `BALTIC_DRY: -48%` | Global transit halt $\to$ airlines $\to$ aerospace tier-1 titanium & avionics suppliers | 2nd-order recall $R@\text{Hop2} \ge 0.85$ on indirect aerospace suppliers |
| **3. 2022 Rate & Duration Shock** | `US10Y_REAL: +2.6%`, `DXY: +14.0%` | Real-rate surge $\to$ tech valuation compression & regional bank HTM bond books | Distress multiplier $\lambda_v$ separates high-debt vs cash-rich tech within 3% error |
| **4. Synthetic Taiwan Foundry Halt** | `FOUNDRY_TW: -70%`, `BALTIC_DRY: +180%` | Wafer fab halt (Hop 1) $\to$ GPU/CPU designers (Hop 2) $\to$ AI hyperscalers & auto OEMs (Hop 3) | Identifies 3-hop auto OEM bottleneck that has ~0.12 calm-regime beta to semiconductors |

---

## 4. Quickstart Guide (Local Execution)

### Prerequisites
- Python 3.12+ (or managed via `uv`)
- Node.js 18+ & npm

### One-Command Setup & Launch
```bash
# Clone and enter directory
cd /Users/dpcubed/projects/contagion-graph

# Run the unified start script (seeds DuckDB, launches FastAPI & Next.js)
./start.sh
```

- **Frontend Web UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI OpenAPI Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 5. Verification Suite & CLI Gates

Every milestone is validated by automated verification gates:

```bash
# Milestone 1: Verify 50-node graph, 2,520-day returns Parquet & DuckDB schema
make seed
# or: python backend/scripts/seed_data.py --verify

# Milestone 2: Run mathematical bit-exact test suite & crisis replays
make test-math

# Milestone 3: Run LLM router, verbatim quote guardrails, and PII sanitizer
make test-llm

# Milestone 4: Run FastAPI integration endpoints & sub-2s performance gate
make test-api
make test-perf

# Run ALL 18 backend verification tests
make test
```
