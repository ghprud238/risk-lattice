"""Factor Registry, units, canonical policies, and validation per Section 16.
"""

from typing import Dict, Literal, Optional
from pydantic import BaseModel, ConfigDict
from app.domain.errors import ContagionDomainException, FailureCode


class FactorDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    factor_id: str
    canonical_unit: Literal["bps", "fraction", "price_fraction", "index_points"]
    description: str
    baseline_series: str
    default_horizon_days: int = 20
    allowed_min: float
    allowed_max: float


FACTOR_REGISTRY: Dict[str, FactorDefinition] = {
    "US10Y_REAL": FactorDefinition(
        factor_id="US10Y_REAL",
        canonical_unit="bps",
        description="US 10-Year Real Yield delta in basis points",
        baseline_series="FRED:DFII10",
        default_horizon_days=20,
        allowed_min=-500.0,
        allowed_max=500.0,
    ),
    "SOFR_SPREAD": FactorDefinition(
        factor_id="SOFR_SPREAD",
        canonical_unit="bps",
        description="SOFR / Overnight funding spread delta in basis points",
        baseline_series="FRED:SOFR",
        default_horizon_days=20,
        allowed_min=-300.0,
        allowed_max=1000.0,
    ),
    "HY_OAS": FactorDefinition(
        factor_id="HY_OAS",
        canonical_unit="bps",
        description="US High Yield Option-Adjusted Spread delta in basis points",
        baseline_series="FRED:BAMLH0A0HYM2",
        default_horizon_days=20,
        allowed_min=-500.0,
        allowed_max=2500.0,
    ),
    "BRENT_CRUDE": FactorDefinition(
        factor_id="BRENT_CRUDE",
        canonical_unit="price_fraction",
        description="Brent Crude oil price fractional return",
        baseline_series="ICE:B",
        default_horizon_days=20,
        allowed_min=-0.80,
        allowed_max=2.00,
    ),
    "COPPER": FactorDefinition(
        factor_id="COPPER",
        canonical_unit="price_fraction",
        description="LME Copper price fractional return",
        baseline_series="LME:CA",
        default_horizon_days=20,
        allowed_min=-0.70,
        allowed_max=1.50,
    ),
    "NAT_GAS": FactorDefinition(
        factor_id="NAT_GAS",
        canonical_unit="price_fraction",
        description="Henry Hub Natural Gas price fractional return",
        baseline_series="NYMEX:NG",
        default_horizon_days=20,
        allowed_min=-0.80,
        allowed_max=3.00,
    ),
    "DXY": FactorDefinition(
        factor_id="DXY",
        canonical_unit="price_fraction",
        description="US Dollar Index fractional change",
        baseline_series="ICE:DX",
        default_horizon_days=20,
        allowed_min=-0.40,
        allowed_max=0.40,
    ),
    "USD_CNH": FactorDefinition(
        factor_id="USD_CNH",
        canonical_unit="price_fraction",
        description="USD/CNH exchange rate fractional change",
        baseline_series="FX:USDCNH",
        default_horizon_days=20,
        allowed_min=-0.30,
        allowed_max=0.50,
    ),
    "VIX": FactorDefinition(
        factor_id="VIX",
        canonical_unit="index_points",
        description="CBOE Volatility Index delta in index points",
        baseline_series="CBOE:VIX",
        default_horizon_days=20,
        allowed_min=-30.0,
        allowed_max=80.0,
    ),
    "BALTIC_DRY": FactorDefinition(
        factor_id="BALTIC_DRY",
        canonical_unit="fraction",
        description="Baltic Dry Index fractional change",
        baseline_series="BALTIC:BDI",
        default_horizon_days=20,
        allowed_min=-0.90,
        allowed_max=3.00,
    ),
    "FOUNDRY_TW": FactorDefinition(
        factor_id="FOUNDRY_TW",
        canonical_unit="fraction",
        description="Taiwan advanced semiconductor foundry capacity fraction delta",
        baseline_series="INDUSTRY:FOUNDRY_TW",
        default_horizon_days=20,
        allowed_min=-1.00,
        allowed_max=0.50,
    ),
    "CANAL_TRANSIT": FactorDefinition(
        factor_id="CANAL_TRANSIT",
        canonical_unit="fraction",
        description="Critical maritime canal (Suez/Panama) throughput volume fraction delta",
        baseline_series="MARITIME:CANAL_FLOW",
        default_horizon_days=20,
        allowed_min=-1.00,
        allowed_max=1.00,
    ),
    "CRITICAL_MINERALS": FactorDefinition(
        factor_id="CRITICAL_MINERALS",
        canonical_unit="fraction",
        description="Rare earths and critical minerals export quota restriction fraction delta",
        baseline_series="INDUSTRY:RARE_EARTHS",
        default_horizon_days=20,
        allowed_min=-1.00,
        allowed_max=0.50,
    ),
    "EURO_GAS_TTF": FactorDefinition(
        factor_id="EURO_GAS_TTF",
        canonical_unit="price_fraction",
        description="Dutch TTF Natural Gas benchmark price fractional return",
        baseline_series="ICE:TFM",
        default_horizon_days=20,
        allowed_min=-0.80,
        allowed_max=4.00,
    ),
    "POWER_GRID_MW": FactorDefinition(
        factor_id="POWER_GRID_MW",
        canonical_unit="fraction",
        description="Industrial baseload electricity and power grid capacity fraction delta",
        baseline_series="GRID:CAPACITY_MW",
        default_horizon_days=20,
        allowed_min=-1.00,
        allowed_max=0.50,
    ),
    "FRA_OIS": FactorDefinition(
        factor_id="FRA_OIS",
        canonical_unit="bps",
        description="Forward Rate Agreement vs Overnight Index Swap interbank spread delta in bps",
        baseline_series="RATES:FRA_OIS",
        default_horizon_days=20,
        allowed_min=-100.0,
        allowed_max=500.0,
    ),
    "EUR_USD_BASIS": FactorDefinition(
        factor_id="EUR_USD_BASIS",
        canonical_unit="bps",
        description="EUR/USD 3-Month Cross-Currency Basis Swap spread delta in basis points",
        baseline_series="FX:EURUSD_XCCY",
        default_horizon_days=20,
        allowed_min=-300.0,
        allowed_max=300.0,
    ),
    "REPO_HAIRCUT": FactorDefinition(
        factor_id="REPO_HAIRCUT",
        canonical_unit="bps",
        description="Securities lending and prime broker repo collateral haircut delta in bps",
        baseline_series="SEC_FIN:REPO_HAIRCUT",
        default_horizon_days=20,
        allowed_min=0.0,
        allowed_max=5000.0,
    ),
    "CP_SPREAD": FactorDefinition(
        factor_id="CP_SPREAD",
        canonical_unit="bps",
        description="Commercial Paper over Treasury tier-1 spread delta in basis points",
        baseline_series="FRED:CP_SPREAD",
        default_horizon_days=20,
        allowed_min=-100.0,
        allowed_max=1000.0,
    ),
    "CLOUD_OUTAGE_SEV": FactorDefinition(
        factor_id="CLOUD_OUTAGE_SEV",
        canonical_unit="index_points",
        description="Hyperscaler and financial cloud infrastructure outage severity index points (0-100)",
        baseline_series="INFRA:CLOUD_OUTAGE",
        default_horizon_days=20,
        allowed_min=0.0,
        allowed_max=100.0,
    ),
    "PORT_DWELL_DAYS": FactorDefinition(
        factor_id="PORT_DWELL_DAYS",
        canonical_unit="index_points",
        description="Major container port average dwell time delta in days",
        baseline_series="PORT:DWELL_DAYS",
        default_horizon_days=20,
        allowed_min=-15.0,
        allowed_max=45.0,
    ),
    "EU_ETS_CARBON": FactorDefinition(
        factor_id="EU_ETS_CARBON",
        canonical_unit="price_fraction",
        description="EU ETS Carbon Emission Allowance price fractional return",
        baseline_series="ICE:CUA",
        default_horizon_days=20,
        allowed_min=-0.80,
        allowed_max=3.00,
    ),
    "DAYS_INVENTORY": FactorDefinition(
        factor_id="DAYS_INVENTORY",
        canonical_unit="fraction",
        description="Corporate buffer inventory days fractional contraction",
        baseline_series="SUPPLY:INVENTORY_BUFFER",
        default_horizon_days=20,
        allowed_min=-1.00,
        allowed_max=1.00,
    ),
    "CASH_CONVERSION_CYCLE": FactorDefinition(
        factor_id="CASH_CONVERSION_CYCLE",
        canonical_unit="fraction",
        description="Supply chain cash conversion cycle stretching fraction delta",
        baseline_series="FIN:CASH_CONVERSION",
        default_horizon_days=20,
        allowed_min=-0.50,
        allowed_max=2.00,
    ),
}


def validate_factor_shock(factor_id: str, unit: str, value: float) -> float:
    """Validates factor registration, unit, and finite bounds per Section 16 & 30.
    Returns normalized fractional impact for the propagation kernel.
    """
    if factor_id not in FACTOR_REGISTRY:
        raise ContagionDomainException(
            code=FailureCode.INPUT_UNIT_MISMATCH,
            message=f"Factor '{factor_id}' is not in the canonical factor registry",
            fields=["factor_id"],
        )
    
    definition = FACTOR_REGISTRY[factor_id]
    if unit != definition.canonical_unit:
        raise ContagionDomainException(
            code=FailureCode.INPUT_UNIT_MISMATCH,
            message=f"Unit mismatch for factor '{factor_id}': expected '{definition.canonical_unit}', got '{unit}'",
            fields=["unit"],
        )
    
    if value < definition.allowed_min or value > definition.allowed_max:
        raise ContagionDomainException(
            code=FailureCode.NONFINITE_RESULT,
            message=f"Value {value} for '{factor_id}' is outside allowed range [{definition.allowed_min}, {definition.allowed_max}]",
            fields=["value"],
        )

    # Conversion to canonical normalized decimal shock:
    if unit == "bps":
        # e.g., 200 bps -> +0.02
        return value / 10000.0
    elif unit == "index_points":
        # e.g. VIX +25 index points -> normalized equity discount / vol impulse
        # 1 VIX point ~ 1.5% equity return shock proxy
        return -(value / 100.0)
    else:
        # price_fraction or fraction is already decimal
        return value
