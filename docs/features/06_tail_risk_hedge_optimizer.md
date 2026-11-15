# Feature 06: Tail-Risk Hedge Optimizer

## Executive Overview
When stress-testing reveals deep portfolio drawdowns (e.g., -$23.45M under a Taiwan blockade), Chief Risk Officers need actionable, capital-efficient hedges. Discretionary hedging often overpays for deep OTM options or suffers severe basis risk.

The **Tail-Risk Hedge Optimizer** formulates hedging as a Mixed-Integer Quadratic/Linear Optimization problem. Under a fixed risk budget (e.g., \$500k to \$2.5M), it selects the optimal combination of proxy instruments (Put options, CDS, Inverse ETFs, Out-of-the-money Call spreads on commodities) to minimize downside CVaR while penalizing basis risk and carry decay.

---

## Mathematical Formulation

### 1. Objective Function
$$\min_{w_{\text{hedge}}} \quad \text{CVaR}_{0.99}\left(L_{\text{unhedged}} + \sum_{k=1}^K w_k \cdot R_{\text{hedge}, k}\right) + \gamma \cdot \text{BasisRisk}(w_{\text{hedge}})$$
subject to:
1. **Budget Constraint**:
   $$\sum_{k=1}^K w_k \cdot \text{Cost}_k \le B_{\text{max}}$$
2. **Cardinality Constraint** (Prevent execution fragmentation):
   $$\sum_{k=1}^K \mathbb{I}(w_k > 0) \le K_{\text{max}} \quad (\text{typically } \le 4 \text{ instruments})$$
3. **Shorting & Concentration Bounds**:
   $$0 \le w_k \le w_{\text{max}}$$

### 2. Candidate Instruments in Library
- **Index Puts**: S&P 500 (SPY 90% Put), Semiconductor ETF (SOXX 85% Put)
- **Credit Protection**: CDX North American Investment Grade 5Y CDS, CDX High Yield CDS
- **Commodity Upside Calls**: Brent Crude Oil Dec Calls (for Strait of Hormuz hedges)
- **Direct Single-Stock Puts**: TSM 80% Put, NVDA 80% Put

---

## Technical Implementation

### File Locations
- **Engine Core**: `backend/app/engine/optimizer.py`
- **Unit Tests**: `backend/tests/unit/test_optimizer.py`
- **API Endpoint**: `POST /api/v1/optimizer/hedge`
- **Frontend Component**: `frontend/src/components/HedgeOptimizer.tsx`

### REST API Schema
```json
{
  "portfolio_notional": 100000000.0,
  "unhedged_pnl": -23450000.0,
  "budget": 500000.0,
  "node_shocks": {
    "TSM": -0.40,
    "NVDA": -0.32,
    "AAPL": -0.26
  }
}
```

### Response:
```json
{
  "budget_allocated": 485000.0,
  "post_hedge_pnl": -9850000.0,
  "cvar_reduction_pct": 58.0,
  "recommended_allocations": [
    {
      "instrument": "SOXX 85% OTM 3M Put",
      "allocation_dollars": 250000.0,
      "contracts": 850,
      "payoff_under_stress": 8200000.0,
      "basis_correlation": 0.92
    },
    {
      "instrument": "CDX NA HY 5Y CDS Protection",
      "allocation_dollars": 235000.0,
      "notional_hedged": 15000000.0,
      "payoff_under_stress": 5400000.0,
      "basis_correlation": 0.84
    }
  ]
}
```

---

## Verification & Test Coverage
- `backend/tests/unit/test_optimizer.py::test_hedge_optimizer_allocation_within_budget` (guarantees allocation $\le B_{\text{max}}$)
- `backend/tests/unit/test_optimizer.py::test_hedge_optimizer_zero_shock_zero_allocation`
- `backend/tests/integration/test_advanced_features_api.py::test_hedge_optimizer_api`
