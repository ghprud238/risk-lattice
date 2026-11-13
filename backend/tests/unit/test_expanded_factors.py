"""Unit tests for Expanded Factor Taxonomy.
Validates the 13 new factors across Physical Choke Points, Banking Plumbing,
Operational/Cyber, and Inventory Buffer dimensions.
"""

import pytest
from app.domain.errors import ContagionDomainException, FailureCode
from app.domain.factor_registry import FACTOR_REGISTRY, validate_factor_shock


def test_physical_choke_point_factors():
    """Validates CANAL_TRANSIT, CRITICAL_MINERALS, EURO_GAS_TTF, and POWER_GRID_MW."""
    # 1. CANAL_TRANSIT: fraction, e.g. -40% Suez/Panama throughput
    norm = validate_factor_shock("CANAL_TRANSIT", "fraction", -0.40)
    assert norm == -0.40

    # 2. CRITICAL_MINERALS: fraction, e.g. -60% rare earth export quota
    norm = validate_factor_shock("CRITICAL_MINERALS", "fraction", -0.60)
    assert norm == -0.60

    # 3. EURO_GAS_TTF: price_fraction, e.g. +150% Dutch TTF natural gas price spike
    norm = validate_factor_shock("EURO_GAS_TTF", "price_fraction", 1.50)
    assert norm == 1.50

    # 4. POWER_GRID_MW: fraction, e.g. -25% power curtailment
    norm = validate_factor_shock("POWER_GRID_MW", "fraction", -0.25)
    assert norm == -0.25


def test_banking_plumbing_and_liquidity_factors():
    """Validates FRA_OIS, EUR_USD_BASIS, REPO_HAIRCUT, and CP_SPREAD in basis points."""
    # 1. FRA_OIS: bps delta, e.g. +75 bps interbank spread
    norm = validate_factor_shock("FRA_OIS", "bps", 75.0)
    assert norm == pytest.approx(0.0075)

    # 2. EUR_USD_BASIS: bps delta, e.g. -85 bps offshore USD funding squeeze
    norm = validate_factor_shock("EUR_USD_BASIS", "bps", -85.0)
    assert norm == pytest.approx(-0.0085)

    # 3. REPO_HAIRCUT: bps delta, e.g. +250 bps prime broker repo margin haircut
    norm = validate_factor_shock("REPO_HAIRCUT", "bps", 250.0)
    assert norm == pytest.approx(0.0250)

    # 4. CP_SPREAD: bps delta, e.g. +120 bps commercial paper spread
    norm = validate_factor_shock("CP_SPREAD", "bps", 120.0)
    assert norm == pytest.approx(0.0120)


def test_operational_and_resilience_factors():
    """Validates CLOUD_OUTAGE_SEV, PORT_DWELL_DAYS, and EU_ETS_CARBON."""
    # 1. CLOUD_OUTAGE_SEV: index points (0-100 severity)
    # Normalized: 80 index points -> -0.80 equity discount impulse
    norm = validate_factor_shock("CLOUD_OUTAGE_SEV", "index_points", 80.0)
    assert norm == pytest.approx(-0.80)

    # 2. PORT_DWELL_DAYS: index points (days of container dwell delta)
    norm = validate_factor_shock("PORT_DWELL_DAYS", "index_points", 20.0)
    assert norm == pytest.approx(-0.20)

    # 3. EU_ETS_CARBON: price_fraction, e.g. +45% carbon allowance price
    norm = validate_factor_shock("EU_ETS_CARBON", "price_fraction", 0.45)
    assert norm == pytest.approx(0.45)


def test_inventory_and_working_capital_factors():
    """Validates DAYS_INVENTORY and CASH_CONVERSION_CYCLE."""
    # 1. DAYS_INVENTORY: fraction, e.g. -30% inventory buffer exhaustion
    norm = validate_factor_shock("DAYS_INVENTORY", "fraction", -0.30)
    assert norm == pytest.approx(-0.30)

    # 2. CASH_CONVERSION_CYCLE: fraction, e.g. +50% working capital cycle stretch
    norm = validate_factor_shock("CASH_CONVERSION_CYCLE", "fraction", 0.50)
    assert norm == pytest.approx(0.50)


def test_factor_validation_rejections():
    """Validates unit mismatch and range violation rejections."""
    # Unit mismatch
    with pytest.raises(ContagionDomainException) as exc1:
        validate_factor_shock("CANAL_TRANSIT", "bps", -0.40)
    assert exc1.value.code == FailureCode.INPUT_UNIT_MISMATCH

    with pytest.raises(ContagionDomainException) as exc2:
        validate_factor_shock("FRA_OIS", "fraction", 50.0)
    assert exc2.value.code == FailureCode.INPUT_UNIT_MISMATCH

    # Out of bounds
    with pytest.raises(ContagionDomainException) as exc3:
        validate_factor_shock("CLOUD_OUTAGE_SEV", "index_points", 150.0)  # max is 100
    assert exc3.value.code == FailureCode.NONFINITE_RESULT

    with pytest.raises(ContagionDomainException) as exc4:
        validate_factor_shock("EURO_GAS_TTF", "price_fraction", 10.0)  # max is 4.0
    assert exc4.value.code == FailureCode.NONFINITE_RESULT
