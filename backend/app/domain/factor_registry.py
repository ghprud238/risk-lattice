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
