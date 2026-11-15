# Feature 13: Endogenous Market Impact & Liquidity Spiral Engine

## Executive Overview
In severe systemic crises, asset prices do not collapse purely due to external fundamental news. Rather, institutional margin calls, capital redemptions, and forced de-grossing trigger **endogenous liquidity spirals**. When funds rush to liquidate large equity or bond blocks into thin order books, their own selling pressure drives prices down, widening bid-ask spreads and triggering secondary margin calls from clearing brokers.

RiskLattice embeds the canonical **Almgren-Chriss (2000)** optimal execution framework coupled with an endogenous fire-sale feedback loop and ISDA SIMM derivative margin call modeling.

---

## Mathematical Formulation

### 1. Almgren-Chriss (2000) Market Impact
For an asset $i$ with Average Daily Volume $\text{ADV}_i$, annualized volatility $\sigma_i$, and liquidated volume $V_i$:
- **Temporary Price Impact (Execution Slippage)**:
  $$I_{\text{temp}, i} = \eta \cdot \sigma_i \cdot \sqrt{\frac{V_i}{\text{ADV}_i \cdot \rho}}$$
  where $\eta = 0.25$ is the temporary impact coefficient and $\rho$ is the market participation rate (typically $10\% - 20\%$).
- **Permanent Price Impact (Adverse Price Discovery)**:
  $$I_{\text{perm}, i} = \gamma \cdot \frac{V_i}{\text{ADV}_i}$$
  where $\gamma = 0.15$ is the permanent impact elasticity.
- **Bid-Ask Spread Blowout**:
  $$S_{\text{stressed}, i} = S_{\text{baseline}, i} \cdot \left(1.0 + 3.0 \cdot \frac{V_i}{\text{ADV}_i}\right)$$

### 2. Endogenous Fire-Sale Feedback Multiplier ($\xi$)
When multiple market participants de-gross concurrently, market depth evaporates:
$$\xi = 1.0 + \kappa \cdot \sum_{i=1}^N \left(\frac{V_i}{\text{ADV}_i}\right)^{1.5}$$
Total realized liquidation loss is amplified by $\xi$:
$$\text{Loss}_{\text{liquidation}} = \xi \cdot \sum_{i=1}^N V_i \cdot \left(\frac{1}{2} S_{\text{stressed}, i} + I_{\text{temp}, i} + \frac{1}{2} I_{\text{perm}, i}\right)$$

### 3. ISDA SIMM Margin Call & Cash Drain
Derivative contracts held by the institution require immediate Variation Margin (VM) transfers and Initial Margin (IM) step-ups under stressed volatility:
$$M_{\text{call}} = \lambda_{\text{simm}} \cdot \text{IM}_0 \cdot \left|\frac{\Delta S}{S_0}\right| \cdot \sqrt{\frac{\text{MPOR}}{10}}$$
where $\text{MPOR} = 10\text{ days}$ is the regulatory Margin Period of Risk.
- **Post-Stress Liquidity Coverage Ratio (LCR)**:
  $$\text{LCR} = \frac{\text{Unencumbered Cash} - \text{Total Liquidity Drain}}{\text{30-Day Net Cash Outflow}} \times 100\%$$
- **Days to Cash Exhaustion**:
  $$\text{Days} = \frac{\text{Available Cash}}{\text{Daily Liquidity Drain Rate}}$$

---

## Technical Implementation

### File Locations
- **Engine Core**: `backend/app/engine/liquidity.py` (AST import isolated)
- **Unit Tests**: `backend/tests/unit/test_liquidity_and_mutation.py`
- **API Endpoint**: `POST /api/v1/liquidity/simulate`
- **Frontend Component**: `frontend/src/components/LiquidityStudio.tsx`

### REST API Schema
```json
{
  "liquidation_pct": 0.20,
  "participation_rate": 0.15,
  "fund_unencumbered_cash": 15000000.0,
  "portfolio_unhedged_pnl": -23450000.0,
  "gross_derivative_notional": 150000000.0
}
```

---

## Verification & Test Coverage
- `backend/tests/unit/test_liquidity_and_mutation.py::test_almgren_chriss_liquidation_and_margin_spiral`
- `backend/tests/integration/test_expansion_services.py::test_liquidity_simulation_endpoint`
- `backend/tests/integration/test_boundary_and_engine.py::test_engine_ast_import_isolation`
