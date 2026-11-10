"""
Mathematical Verification Suite for ContagionGraph.
PRD Milestone 2 Verification Gate:
- Huber robust regression calibration
- Bit-exact 4-hop propagation reproducibility
- Student-t copula PCG64(42) bit-exact reproducibility
- 4 Historical Crisis Replay benchmark tests
- Kupiec POF test (LR_POF < 3.84 at p=0.05)
- Hop-2/Hop-3 Discovery Lift
"""
import pytest
import numpy as np
from app.db.database import db_manager
from app.engine.calibrator import EdgeCalibrator
from app.engine.propagator import ContagionPropagator
from app.engine.risk_metrics import TailRiskEngine
from app.engine.backtest import BacktestEngine, HISTORICAL_CRISIS_SCENARIOS


@pytest.fixture(scope="module")
def calibrator():
    return EdgeCalibrator(db_manager)


@pytest.fixture(scope="module")
def propagator(calibrator):
    return ContagionPropagator(calibrator=calibrator)


@pytest.fixture(scope="module")
def backtest_engine():
    return BacktestEngine(db_manager)


def test_huber_regression_bounds(calibrator):
    """Verifies Huber regression produces bounded betas within [-1.0, 1.0]."""
    betas = calibrator.calibrate_huber_beta("NVDA", ["DXY", "VIX", "USD_CNH"])
    for f, b in betas.items():
        assert -1.0 <= b <= 1.0, f"Beta for {f} exceeded bounds: {b}"


def test_multihop_propagation_bit_exact(propagator):
    """
    Verifies that identical initial shock s^(0) produces bit-for-bit identical output.
    Zero floating point drift allowed.
    """
    test_shock = {"FOUNDRY_TW": -0.70, "BALTIC_DRY": 1.20, "US10Y_REAL": 0.02}

    res1 = propagator.propagate(test_shock, scenario_name="Bit Exact Test 1")
    res2 = propagator.propagate(test_shock, scenario_name="Bit Exact Test 2")

    assert len(res1.node_shocks) == len(res2.node_shocks)
    for nid in res1.node_shocks:
        s1 = res1.node_shocks[nid]
        s2 = res2.node_shocks[nid]
        assert s1.cumulative_shock == s2.cumulative_shock, f"Mismatch in cumulative shock for {nid}: {s1.cumulative_shock} vs {s2.cumulative_shock}"
        assert s1.hop1 == s2.hop1
        assert s1.hop2 == s2.hop2
        assert s1.hop3 == s2.hop3
        assert s1.hop4 == s2.hop4

    assert res1.portfolio_pnl == res2.portfolio_pnl


def test_multihop_clamping_and_distress_multipliers(propagator):
    """Verifies that cumulative shock is strictly clamped to [-0.95, +1.50] and lambda_v amplifies distress."""
    extreme_shock = {nid: -2.0 for nid in ["US10Y_REAL", "HY_OAS", "SOFR_SPREAD", "FOUNDRY_TW"]}
    res = propagator.propagate(extreme_shock, scenario_name="Extreme Stress Test")

    for nid, s in res.node_shocks.items():
        assert s.cumulative_shock >= -0.95, f"{nid} breached lower clamp bound: {s.cumulative_shock}"
        assert s.cumulative_shock <= 1.50, f"{nid} breached upper clamp bound: {s.cumulative_shock}"

    # Verify high-debt Ford and PACW have lambda > 1.0
    f_res = res.node_shocks["F"]
    pacw_res = res.node_shocks["PACW"]
    nvda_res = res.node_shocks["NVDA"]

    assert f_res.distress_multiplier > 1.2, f"Ford distress multiplier expected > 1.2, got {f_res.distress_multiplier}"
    assert pacw_res.distress_multiplier > 1.2, f"PacWest distress multiplier expected > 1.2, got {pacw_res.distress_multiplier}"
    assert nvda_res.distress_multiplier == 1.0, f"Cash-rich NVDA expected lambda=1.0, got {nvda_res.distress_multiplier}"


def test_student_t_copula_bit_exact():
    """Verifies that TailRiskEngine with PCG64(42) guarantees bit-exact reproducible CVaR."""
    portfolio = {"NVDA": 0.25, "TSM": 0.25, "DAL": 0.25, "XOM": 0.25}

    engine1 = TailRiskEngine(df_t=4.0, num_simulations=5000, seed=42)
    risk1 = engine1.compute_portfolio_risk(portfolio, db=db_manager)

    engine2 = TailRiskEngine(df_t=4.0, num_simulations=5000, seed=42)
    risk2 = engine2.compute_portfolio_risk(portfolio, db=db_manager)

    assert risk1.var_99 == risk2.var_99, f"VaR mismatch: {risk1.var_99} vs {risk2.var_99}"
    assert risk1.cvar_99 == risk2.cvar_99, f"CVaR mismatch: {risk1.cvar_99} vs {risk2.cvar_99}"
    assert risk1.copula_to_gaussian_ratio == risk2.copula_to_gaussian_ratio


def test_all_four_crisis_replays(backtest_engine):
    """
    Replays all 4 historical and synthetic crisis scenarios from PRD Section 6.2:
    1. 2008 Credit Freeze (CVaR capture >= 90%)
    2. 2020 Mobility & Supply Halt (2nd-order recall R@Hop2 >= 0.85)
    3. 2022 Rate & Duration Shock (Distress multiplier separates debt within 3%)
    4. Synthetic Taiwan Foundry Halt (Bottleneck with calm-regime beta ~0.12)
    """
    reports = backtest_engine.run_all_crisis_replays()
    assert len(reports) == 4, f"Expected 4 crisis reports, got {len(reports)}"

    for report in reports:
        assert report.metric_achieved, (
            f"Scenario '{report.scenario_name}' failed target benchmark: "
            f"Achieved={report.benchmark_value}, Target={report.comparison_value}, Details={report.details}"
        )


def test_kupiec_pof_validation(backtest_engine):
    """
    Kupiec Proportion of Failures (POF) Likelihood Ratio Test:
    Evaluates whether 99% VaR breaches stay statistically indistinguishable
    from 1% during stress windows (LR_POF < 3.84 at p=0.05).
    """
    result = backtest_engine.run_kupiec_pof_test(p=0.01)
    assert result.passed, f"Kupiec POF test failed: LR_stat={result.lr_stat} >= 3.8415 (p_value={result.p_value})"
    assert result.lr_stat < 3.8415


def test_hop2_hop3_discovery_lift(backtest_engine):
    """
    Hop-2/Hop-3 Discovery Lift:
    Verifies that multi-hop contagion propagation identifies indirect choke points
    (such as auto OEMs downstream of wafer fabs) that are missed by 60-day Pearson correlation.
    """
    lift = backtest_engine.run_discovery_lift()
    assert len(lift.indirect_nodes_identified) >= 2, f"Expected >=2 indirect nodes, got {lift.indirect_nodes_identified}"
    assert lift.f1_score >= 0.80, f"Expected F1 >= 0.80, got {lift.f1_score}"
    assert -0.15 <= lift.calm_beta_nvda_to_auto <= 0.25, f"Expected dormant calm beta ~0.12, got {lift.calm_beta_nvda_to_auto}"
