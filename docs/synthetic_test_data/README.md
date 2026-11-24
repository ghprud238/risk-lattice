# RiskLattice Synthetic Testing Fixtures & Benchmark Catalog

This directory contains production-grade, mathematically verified synthetic datasets for inputs and expected outputs across the 9 core institutional testing use cases.

These fixtures allow developers, quantitative researchers, QA engineers, and external auditors to validate RiskLattice calculation engines, APIs, and front-end visualizations against deterministic ground truth without requiring live market feeds or proprietary data.

All outputs were generated using the pure Python quantitative risk engine under strict Federal Reserve SR 11-7 model governance and ADR-002 AST architectural isolation (zero DB, HTTP, or LLM imports).

---

## Catalog Index

| Fixture ID | Domain | Input File | Output File | Verification Engine |
| :--- | :--- | :--- | :--- | :--- |
| **Case 01** | Geopolitical Tech Disruption | [`01_taiwan_foundry_shock_input.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/01_taiwan_foundry_shock_input.json) | [`01_taiwan_foundry_shock_output.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/01_taiwan_foundry_shock_output.json) | `ContagionPropagator`, `TailRiskEngine`, `compute_portfolio_valuation` |
| **Case 02** | Maritime Radar & Choke Point | [`02_suez_maritime_blockade_input.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/02_suez_maritime_blockade_input.json) | [`02_suez_maritime_blockade_output.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/02_suez_maritime_blockade_output.json) | `AISThreatEngine`, `ChokePointTelemetry` |
| **Case 03** | Portfolio Ingestion (Aladdin) | [`03_institutional_portfolio_aladdin_input.csv`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/03_institutional_portfolio_aladdin_input.csv) | [`03_institutional_portfolio_aladdin_output.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/03_institutional_portfolio_aladdin_output.json) | Rule P-01 Privacy Scrubber, CSV Normalizer |
| **Case 04** | Multi-Asset Convexity & Greeks | [`04_multi_asset_derivatives_port_input.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/04_multi_asset_derivatives_port_input.json) | [`04_multi_asset_derivatives_port_output.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/04_multi_asset_derivatives_port_output.json) | `evaluate_any_instrument`, `OptionPosition`, `BondPosition`, `CDSPosition`, `PrivateCreditPosition`, `CLOTranchePosition` |
| **Case 05** | Tail-Risk Hedge Optimizer | [`05_tail_risk_hedge_optimizer_input.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/05_tail_risk_hedge_optimizer_input.json) | [`05_tail_risk_hedge_optimizer_output.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/05_tail_risk_hedge_optimizer_output.json) | `TailRiskHedgeOptimizer` (SLSQP Solver) |
| **Case 06** | Algorithmic Reverse Stress Test | [`06_reverse_stress_testing_input.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/06_reverse_stress_testing_input.json) | [`06_reverse_stress_testing_output.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/06_reverse_stress_testing_output.json) | `ReverseStressTester` (Minimal $L_2$ Inversion) |
| **Case 07** | Liquidity & Fire-Sale Spiral | [`07_almgren_chriss_liquidity_input.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/07_almgren_chriss_liquidity_input.json) | [`07_almgren_chriss_liquidity_output.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/07_almgren_chriss_liquidity_output.json) | `EndogenousLiquidityEngine` (Almgren-Chriss & ISDA SIMM) |
| **Case 08** | Supply Chain Mutation & ROI | [`08_supply_chain_mutation_input.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/08_supply_chain_mutation_input.json) | [`08_supply_chain_mutation_output.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/08_supply_chain_mutation_output.json) | `GraphMutationEngine` (`SEVER_EDGE`, `REWEIGHT_EDGE`) |
| **Case 09** | Cryptographic Audit Sign-off | [`09_four_eyes_audit_vault_input.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/09_four_eyes_audit_vault_input.json) | [`09_four_eyes_audit_vault_output.json`](file:///Users/dpcubed/projects/risk-lattice/docs/synthetic_test_data/09_four_eyes_audit_vault_output.json) | SHA-256 Envelope Hasher, Four-Eyes State Machine |

---

## Detailed Specification & Mathematical Ground Truth

### 1. Taiwan Semiconductor Foundry Disruption (`01_*`)
- **Premise**: Naval exclusion zone in Taiwan Strait shocks Taiwan advanced wafer exports by $-70\%$ with Baltic Dry shipping rate spike $+120\%$.
- **Mitigating Factors**: Company inventory buffers override default decay (NVDA: 45 days, AAPL: 30 days, MSFT: 60 days). Over a 20-day horizon, buffered companies experience zero supply shock.
- **Expected Outputs**:
  - Total Active Nodes Affected: `16`
  - Critical Paths: `['BALTIC_DRY', 'LOGISTICS_PORT_LA', 'AVIONICS_DSP_SUP', 'BA']` and `['FOUNDRY_TW', 'TSM']`.
  - Copula Tail Risk: 99% VaR = `5.44%`, 99% CVaR = `6.67%`, Tail Ratio (Copula-to-Gaussian) = `10.66x` (Student-$t$ with $\nu = 4.0$).
  - Multi-Hop PnL Attribution:
    - Order 1 (Direct Seeds): $-\$903,000.00$
    - Order 2 (Tier-1 Suppliers): $+\$351,370.00$ (freight upside)
    - Order 3-4 (Network Re-propagation): $+\$127,610.00$
    - Stressed Portfolio PnL: $-\$424,020.00$ on $\$20,000,000.00$ notional ($-2.12\%$).

### 2. Suez Maritime Blockade & AIS Telemetry (`02_*`)
- **Premise**: Houthi anti-ship missile activity near Bab-el-Mandeb collapses transit speed to $2.8$ knots (baseline $12.0$) and inflates vessel queue to $118$ (baseline $85$).
- **Expected Outputs**:
  - Non-linear Congestion Index: `4.59`
  - Demurrage Charter Rate Spike: $+161.6\%$
  - Disruption Probability: `0.999`
  - Global Systemic Vulnerability Index (SVI): `20.0 / 100.0`
  - Direct Macro Impulses: Decaying supply shock into European manufacturing hubs (`PORT_RTM: -0.8775`, `ASML: -0.7459`, `BMW: -0.634`, `F: -0.5389`).

### 3. BlackRock Aladdin CSV Portfolio Ingestion (`03_*`)
- **Premise**: Standard institutional multi-column CSV containing $\$20,000,000.00$ gross tech portfolio across 10 global issuers.
- **Expected Outputs**:
  - Normalized Portfolio Weights: Sums strictly to `1.0000` (e.g. NVDA: 15%, AAPL: 12.5%, MSFT: 11%, TSM: 10%).
  - Privacy Compliance (Rule P-01): Absolute dollar amounts and share quantities scrubbed before LLM prompt assembly.

### 4. Multi-Asset Convexity & Greeks (`04_*`)
- **Premise**: Mixed cross-asset institutional book ($13,150,000.00$ notional) subjected to multi-node stress:
  - Equity: NVDA LONG ($\$2\text{M}$, shock $-28\%$)
  - Option: NVDA OTM Put ($\$150\text{k}$, spot $125 \to 90$, IV $45\% \to 54.8\%$)
  - Bond: TSM 6.8y Senior Bond ($\$3\text{M}$, duration 6.8y, convexity 55.0, spread widening $+448$ bps)
  - CDS: INTC 5Y Protection BUY ($\$5\text{M}$, spread $120 \to 208$ bps)
  - Private Credit: Senior Secured Direct Loan ($\$2\text{M}$, leverage $4.8\text{x} \to 8.0\text{x}$, covenant ceiling $4.5\text{x}$)
  - CLO Tranche: BBB Mezzanine $[9\% - 18\%]$ ($\$1\text{M}$, underlying pool loss $25\%$)
- **Expected Outputs**:
  - Net Portfolio PnL: $-\$2,279,277.78$ ($-17.33\%$ return)
  - OTM Put Payoff: $+\$517,884.55$ ($+345.26\%$ return, non-linear Gamma hedge)
  - Private Credit Impairment: $-\$700,000.00$ ($-35.0\%$ writedown on covenant breach)
  - CLO Tranche Impairment: $-\$1,000,000.00$ ($-100\%$ complete wipeout of mezzanine tranche)

### 5. Capital-Constrained Tail-Risk Hedge Optimizer (`05_*`)
- **Premise**: Unhedged portfolio suffering $-\$3,850,000.00$ loss under contagion; solve for optimal allocation across 3 hedge instruments subject to a $\$400,000.00$ capital budget.
- **Expected Outputs**:
  - Budget Allocated: $\$399,999.81$ (remaining $\$0.19$)
  - Optimal Instrument Allocation:
    - `SOXX_PUT` (TSM ETF Puts): $\$9,813,323.66$ notional, cost $\$372,906.30$, PnL protection $+\$6,354,127.07$.
    - `NVDA_PUT` (NVIDIA Puts): $\$645,057.59$ notional, cost $\$27,092.42$, PnL protection $+\$379,293.86$.
    - `F_CDS_5Y`: $\$0.00$ (inferior protection elasticity per dollar).
  - Net Hedged PnL: $+\$2,483,437.16$ ($\$6,333,437.16$ PnL turnaround).
  - 99% CVaR Relief: $100\%$ elimination of tail deficit.

### 6. Algorithmic Reverse Stress Testing (`06_*`)
- **Premise**: Invert the multi-factor risk propagation engine to find the minimal $L_2$-norm shock vector causing a $\ge 15.0\%$ portfolio breach.
- **Expected Outputs**:
  - Minimal $L_2$ Norm: `0.1725`
  - Primary Vulnerability Factor: `FOUNDRY_TW` (contributes $26.8\%$ of total loss with minimal shock $-8.93\%$).
  - Second Vulnerability: `HY_OAS` (contributes $21.2\%$ of total loss with minimal shock $-7.94\%$).

### 7. Endogenous Liquidity & Almgren-Chriss Fire Sale (`07_*`)
- **Premise**: Institutional fund forced to liquidate $25\%$ of positions ($\$5,750,000.00$ notional) within a single day during market stress to meet ISDA SIMM derivative margin calls.
- **Expected Outputs**:
  - Market Impact Slippage: $-\$132,059.54$ ($2.30\%$ blended discount).
  - Margin Call Drain: $\$14,380,000.00$ total cash drain ($\$5.0\text{M}$ IM step-up + $\$9.38\text{M}$ VM deficit).
  - Post-Stress Liquidity Coverage Ratio (LCR): `104.3%`.
  - Cash Exhaustion: `15.3 days` remaining buffer.

### 8. What-If Supply Chain Mutation & ROI (`08_*`)
- **Premise**: Supply chain topological re-design to mitigate semiconductor supply shocks:
  - `REWEIGHT_EDGE`: `FOUNDRY_TW -> TSM` reduced from $0.85$ to $0.30$ (Capex: $\$100\text{k}$, Lead Time: 12 months).
  - `SEVER_EDGE`: `FOUNDRY_TW -> AMD` severed to $0.00$ via secondary packaging qualification (Capex: $\$50\text{k}$, Lead Time: 6 months).
- **Expected Outputs**:
  - Initial Unmitigated Loss: $-\$424,030.00$
  - Mutated Hardened Loss: $-\$156,444.88$
  - Capital Savings: $+\$267,585.12$
  - Resilience ROI Multiple: `1.78x` net return on $\$150,000.00$ capex.
  - Financial Viability: `true` (ROI $\ge 1.5\text{x}$).

### 9. Four-Eyes Cryptographic Audit Sign-off (`09_*`)
- **Premise**: Federal Reserve CCAR 2026 stress testing run requires dual-key cryptographic sealing by Senior Analyst (Preparer) and Chief Risk Officer (Approver).
- **Expected Outputs**:
  - Cryptographic Seal: Deterministic SHA-256 hash sealing `run_id`, `model_version`, `cvar_99`, `preparer`, and `approver`.
  - Regulatory Status: `APPROVED_AND_LOCKED`, Fed SR 11-7 Model Governance `VERIFIED_PASS`.

---

## How to Regenerate Fixtures

Run the generator script directly from the workspace root:

```bash
cd /Users/dpcubed/projects/risk-lattice
.venv/bin/python docs/synthetic_test_data/generate_synthetic_test_data.py
```

## Running Automated CI Regression Tests

To verify that the current engine reproduces these synthetic fixtures bit-for-bit:

```bash
cd /Users/dpcubed/projects/risk-lattice
.venv/bin/pytest backend/tests/integration/test_synthetic_data_fixtures.py -v
```
