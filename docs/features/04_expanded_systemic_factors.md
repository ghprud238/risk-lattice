# Feature 04: Expanded Systemic Risk Factors

## Executive Overview
Traditional risk models calibrate shocks exclusively against standard equity benchmarks (S&P 500, MSCI World). However, real-world corporate crises are triggered by complex physical, monetary plumbing, and operational systemic shocks. 

RiskLattice defines **12 specialized systemic risk factors** across maritime choke points, banking plumbing, and operational resiliency channels, each with validated shock bounds, transmission elasticity, and regulatory tagging.

---

## The 12 Systemic Risk Factors

### 1. Physical Maritime & Geographical Choke Points
1. **Taiwan Strait Maritime Corridor (`GEO_TAIWAN_STRAIT`)**:
   - Shock Channel: Semiconductor wafer export halt, container shipping rerouting around Luzon Strait.
   - Default Shock Range: $[-0.10, -0.60]$. Target: Semiconductor fabs and consumer electronics.
2. **Strait of Malacca (`GEO_MALACCA`)**:
   - Shock Channel: Middle East crude oil delivery disruption to East Asia; bunker fuel cost surge.
   - Default Shock Range: $[-0.05, -0.45]$. Target: Asian petrochemicals, global maritime shippers.
3. **Strait of Hormuz (`GEO_HORMUZ`)**:
   - Shock Channel: Severe energy supply shock; Brent crude spike $>40\%$; jet fuel rationing.
   - Default Shock Range: $[-0.10, -0.50]$. Target: Airlines, utilities, industrial chemicals.
4. **Suez Canal / Bab-el-Mandeb (`GEO_SUEZ`)**:
   - Shock Channel: Asia-Europe transit diversion around Cape of Good Hope (+14 days transit, +300% freight rates).
   - Default Shock Range: $[-0.05, -0.35]$. Target: European retail, global auto parts.
5. **Panama Canal Drought / Transit Restriction (`GEO_PANAMA`)**:
   - Shock Channel: US Gulf LNG and grain bulk carrier draft restrictions; demurrage fee escalation.
   - Default Shock Range: $[-0.05, -0.25]$. Target: Agricultural exporters, LNG carriers.

### 2. Monetary Plumbing & Interbank Liquidity Channels
6. **SOFR / Secured Funding Rate Spike (`PLUMB_SOFR_SPIKE`)**:
   - Shock Channel: Year-end repo market squeeze; primary dealer balance sheet capacity exhaustion.
   - Default Shock Range: $[+50\text{bps}, +350\text{bps}]$. Target: Leveraged loans, REITs, hedge funds.
7. **Tri-Party Repo Haircut Escalation (`PLUMB_REPO_HAIRCUT`)**:
   - Shock Channel: Collateral eligibility tightening; non-agency MBS and corporate bond haircuts doubling from $5\%$ to $15\%$.
   - Default Shock Range: $[+2\%, +15\%]$. Target: Non-bank financial intermediaries (NBDIs).
8. **Cross-Currency Basis Swap Widening (`PLUMB_EUR_USD_BASIS`)**:
   - Shock Channel: Offshore USD funding crunch; European and Japanese bank dollar liquidity freeze.
   - Default Shock Range: $[-20\text{bps}, -150\text{bps}]$. Target: Foreign multinational balance sheets.

### 3. Operational, Resiliency & Sovereign Channels
9. **Critical Infrastructure Cyber Disruption (`OPS_CYBER_GRID`)**:
   - Shock Channel: Regional power grid or financial clearing system disruption (Fedwire/SWIFT outage).
   - Default Shock Range: $[-0.15, -0.50]$. Target: Commercial banking, manufacturing plants.
10. **Tier-1 Cloud Provider Regional Outage (`OPS_CLOUD_OUTAGE`)**:
    - Shock Channel: Multi-AZ cloud infrastructure failure; automated execution and API downtime.
    - Default Shock Range: $[-0.05, -0.25]$. Target: SaaS platforms, digital fintechs.
11. **Sovereign Sanctions & Asset Freezes (`OPS_SOVEREIGN_SANCTIONS`)**:
    - Shock Channel: Secondary sanctions; correspondent banking cut-offs; frozen sovereign reserves.
    - Default Shock Range: $[-0.20, -0.80]$. Target: Emerging market multinationals, state-owned enterprises.
12. **Critical Mineral Export Restrictions (`OPS_RARE_EARTH_BAN`)**:
    - Shock Channel: Neodymium, dysprosium, and gallium export quotas; EV motor and defense sensor production halt.
    - Default Shock Range: $[-0.10, -0.45]$. Target: Defense contractors, EV manufacturers.

---

## Technical Implementation

### File Locations
- **Factor Definitions**: `backend/app/engine/factors.py`
- **Unit Tests**: `backend/tests/unit/test_expanded_factors.py` (Validates ranges, schema, elasticity)
- **API Endpoint**: `GET /api/v1/factors/catalog`

### Code Architecture
```python
@dataclass(frozen=True)
class SystemicFactor:
    factor_id: str
    name: str
    category: str
    min_shock: float
    max_shock: float
    unit: str
    description: str
    affected_sectors: List[str]

FACTORS_REGISTRY = {
    "GEO_TAIWAN_STRAIT": SystemicFactor(
        factor_id="GEO_TAIWAN_STRAIT",
        name="Taiwan Strait Maritime Blockade",
        category="PHYSICAL_CHOKE_POINT",
        min_shock=-0.60,
        max_shock=-0.05,
        unit="PCT_CAPACITY_LOSS",
        description="Naval blockade cutting off 65% of global advanced semiconductor packaging.",
        affected_sectors=["Semiconductors", "Consumer Electronics", "Automotive"]
    ),
    # Additional 11 factors...
}
```

---

## Verification & Test Coverage
- `backend/tests/unit/test_expanded_factors.py::test_physical_choke_point_factors`
- `backend/tests/unit/test_expanded_factors.py::test_banking_plumbing_and_liquidity_factors`
- `backend/tests/unit/test_expanded_factors.py::test_operational_and_resilience_factors`
- `backend/tests/unit/test_expanded_factors.py::test_factor_validation_rejections` (verifies out-of-bounds rejection)
