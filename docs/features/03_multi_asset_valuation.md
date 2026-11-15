# Feature 03: Multi-Asset Non-Linear Valuation Engine

## Executive Overview
Stress scenarios do not impact all asset classes linearly. While equities experience percentage drawdowns, derivatives exhibit non-linear Delta-Gamma-Vega responses, corporate bonds suffer credit spread widening with duration-convexity price decay, credit default swaps experience hazard rate jumps, and private credit assets trigger covenant breach haircuts. 

RiskLattice provides a full suite of analytical non-linear pricing models across equities, options, corporate debt, CDS, FX forwards, private credit, and collateralized loan obligations (CLOs).

---

## Instrument Pricing Formulations

### 1. Equity Derivatives (Black-Scholes-Merton)
For European Put/Call options under spot shock $\Delta S$:
$$V(S + \Delta S) \approx V(S) + \Delta \cdot \Delta S + \frac{1}{2}\Gamma (\Delta S)^2 + \mathcal{V} \cdot \Delta \sigma + \Theta \cdot \Delta t$$
- Long Out-of-the-Money Puts provide convex portfolio protection as $\Gamma > 0$ and Vega $\mathcal{V} > 0$ during market crashes.

### 2. Corporate Bonds (Modified Duration & Convexity with Merton Spread Widening)
Corporate bond pricing accounts for both interest rate shocks $\Delta y$ and credit spread blowout $\Delta s$:
$$\frac{\Delta P}{P} = -D_{\text{mod}} \cdot (\Delta y + \Delta s) + \frac{1}{2} C \cdot (\Delta y + \Delta s)^2$$
Credit spread widening $\Delta s$ is linked to equity drawdown $\Delta E / E$ via Merton's structural model:
$$\Delta s = \beta_{\text{credit}} \cdot |\Delta E / E| \cdot \sigma_{\text{asset}}$$

### 3. Credit Default Swaps (CDS)
For protection buyers holding CDS contracts on distressed entities:
$$\Delta \text{MtM}_{\text{CDS}} = \text{Notional} \cdot \text{RPV01} \cdot \Delta \lambda_{\text{hazard}}$$
where hazard rate jump $\Delta \lambda = \frac{\Delta s}{1 - R}$ and $R$ is the expected recovery rate (standard $40\%$).

### 4. Private Credit & Direct Lending
Private credit facilities lack continuous secondary market pricing. The model applies structural covenant breach tests:
$$\text{Haircut} = \begin{cases}
0.0 & \text{if Leverage} \le 5.0\times \\
15\% & \text{if } 5.0\times < \text{Leverage} \le 6.5\times \quad \text{(Technical Breach)} \\
35\% & \text{if Leverage} > 6.5\times \quad \text{(Payment Default / Restructuring)}
\end{cases}$$

### 5. Structured Credit (CLO Tranches)
Tranche loss absorption follows the strict subordination waterfall:
$$\text{Loss}_{\text{Tranche}} = \min\left(1.0, \max\left(0.0, \frac{\text{Collateral Loss} - \text{Attachment}}{\text{Detachment} - \text{Attachment}}\right)\right)$$

---

## Technical Implementation

### File Locations
- **Engine Core**: `backend/app/engine/instruments.py`
- **Unit Tests**: `backend/tests/unit/test_multi_asset_instruments.py` (8 test suites covering each instrument)
- **API Endpoint**: `POST /api/v1/portfolio/ingest`, `POST /api/v1/stress/simulate`

### Code Architecture
```python
from dataclasses import dataclass
from enum import Enum
import numpy as np

class AssetClass(str, Enum):
    EQUITY = "EQUITY"
    OPTION = "OPTION"
    CORPORATE_BOND = "CORPORATE_BOND"
    CDS = "CDS"
    PRIVATE_CREDIT = "PRIVATE_CREDIT"
    FX_FORWARD = "FX_FORWARD"
    CLO_TRANCHE = "CLO_TRANCHE"

@dataclass
class Position:
    asset_id: str
    asset_class: AssetClass
    notional: float
    spot_price: float
    delta: float = 1.0
    gamma: float = 0.0
    vega: float = 0.0
    duration: float = 0.0
    convexity: float = 0.0
    covenant_threshold: float = 0.0

def price_position_pnl(pos: Position, shock_pct: float, vol_spike: float = 0.20) -> float:
    if pos.asset_class == AssetClass.EQUITY:
        return pos.notional * shock_pct
    elif pos.asset_class == AssetClass.OPTION:
        ds = pos.spot_price * shock_pct
        pnl = (pos.delta * ds + 0.5 * pos.gamma * (ds ** 2) + pos.vega * vol_spike)
        return pnl * (pos.notional / pos.spot_price)
    elif pos.asset_class == AssetClass.CORPORATE_BOND:
        spread_widening = abs(shock_pct) * 0.03
        return pos.notional * (-pos.duration * spread_widening + 0.5 * pos.convexity * (spread_widening ** 2))
    # Additional asset class evaluations...
```

---

## Verification & Test Coverage
- `backend/tests/unit/test_multi_asset_instruments.py::test_equity_valuation_long_and_short`
- `backend/tests/unit/test_multi_asset_instruments.py::test_protective_put_tail_risk_hedge`
- `backend/tests/unit/test_multi_asset_instruments.py::test_corporate_bond_duration_convexity_and_distress`
- `backend/tests/unit/test_multi_asset_instruments.py::test_cds_buy_protection_hazard_rate_jump`
- `backend/tests/unit/test_multi_asset_instruments.py::test_private_credit_covenant_breach_and_haircut`
- `backend/tests/unit/test_multi_asset_instruments.py::test_clo_tranche_waterfall_loss_absorption`
