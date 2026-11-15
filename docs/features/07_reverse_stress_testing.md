# Feature 07: Algorithmic Reverse Stress Testing

## Executive Overview
Under Federal Reserve SR 11-7 and Basel Committee principles for sound stress testing, institutions must not only run forward hypothetical scenarios, but also conduct **Reverse Stress Testing**: identifying the exact, minimal combination of macroeconomic, geopolitical, and supply chain shocks that would cause the institution to breach its capital adequacy thresholds or insolvency limits.

RiskLattice features an automated inverse mathematical solver that identifies hidden vulnerabilities and critical single-point-of-failure clusters.

---

## Mathematical Formulation

### 1. The Inverse Problem
Given a critical portfolio loss threshold $L_{\text{target}}$ (e.g., -\$25M or -25% drawdown on equity capital), solve:
$$\min_{s \in [-1, 0]^N} \quad \|s\|_2^2 + \alpha \sum_{i=1}^N \frac{|s_i|}{\text{HistoricalVol}_i}$$
subject to:
$$\text{PortfolioPnL}\left( \text{Propagate}(s, W, \lambda) \right) \le L_{\text{target}}$$
where $\|s\|_2$ penalizes implausibly severe shocks, finding the most plausible minimal impulse vector that triggers disaster.

### 2. Algorithmic Solver
Because the multi-hop propagation with non-linear distress multipliers is non-convex, the engine employs a hybrid gradient-free optimization procedure:
1. **Eigen-Centrality Initialization**: Evaluates the Perron-Frobenius eigenvector of $W$ to identify structurally dominant bottlenecks.
2. **Binary Search & Ray Marching**: Projects along dominant vulnerability rays to locate the minimal boundary crossing point.
3. **Local Coordinate Refinement**: Tightens shocks around the boundary within $<250\text{ms}$.

---

## Technical Implementation

### File Locations
- **Engine Core**: `backend/app/engine/optimizer.py`
- **Unit Tests**: `backend/tests/unit/test_optimizer.py`
- **API Endpoint**: `POST /api/v1/reverse-stress/solve`

### REST API Schema
```json
{
  "portfolio_notional": 100000000.0,
  "loss_threshold": -25000000.0,
  "candidate_nodes": ["TSM", "NVDA", "AAPL", "F", "2317_TW"]
}
```

### Response:
```json
{
  "solved": true,
  "minimal_shock_magnitude": 0.285,
  "critical_impulses": {
    "TSM": -0.285,
    "2317_TW": -0.192
  },
  "resulting_pnl": -25042000.0,
  "bottleneck_insight": "A 28.5% capacity disruption at TSMC alone is sufficient to trigger the -$25M loss threshold due to 2nd-order cascade through Foxconn and Nvidia."
}
```

---

## Verification & Test Coverage
- `backend/tests/unit/test_optimizer.py::test_reverse_stress_tester_finds_minimal_breaking_point`
- `backend/tests/integration/test_advanced_features_api.py::test_reverse_stress_api`
