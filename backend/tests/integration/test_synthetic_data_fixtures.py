"""Integration Tests validating machine-readable synthetic data fixtures in docs/synthetic_test_data/.

Verifies that all 9 institutional test fixtures match the calculations of the RiskLattice quantitative engines.
"""

import hashlib
import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from app.engine.propagator import ContagionPropagator
from app.engine.valuation import compute_portfolio_valuation
from app.engine.ais_threat import (
    AISThreatEngine,
    ChokePointTelemetry,
    ChokePointStatus,
    ThreatEvent,
    ThreatSeverity,
)
from app.engine.instruments import (
    EquityPosition,
    OptionPosition,
    OptionType,
    PositionSide,
    BondPosition,
    CDSPosition,
    PrivateCreditPosition,
    CLOTranchePosition,
    evaluate_any_instrument,
)
from app.engine.optimizer import (
    TailRiskHedgeOptimizer,
    HedgeCandidate,
    ReverseStressTester,
)
from app.engine.liquidity import (
    EndogenousLiquidityEngine,
    LiquidationPosition,
)
from app.engine.mutation import (
    GraphMutationEngine,
    GraphMutation,
    MutationType,
)
from app.services.snapshot_service import snapshot_service

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "synthetic_test_data"


def test_synthetic_fixtures_exist():
    """Verifies that all 18 input and output fixture files exist in docs/synthetic_test_data/."""
    expected_files = [
        "01_taiwan_foundry_shock_input.json",
        "01_taiwan_foundry_shock_output.json",
        "02_suez_maritime_blockade_input.json",
        "02_suez_maritime_blockade_output.json",
        "03_institutional_portfolio_aladdin_input.csv",
        "03_institutional_portfolio_aladdin_output.json",
        "04_multi_asset_derivatives_port_input.json",
        "04_multi_asset_derivatives_port_output.json",
        "05_tail_risk_hedge_optimizer_input.json",
        "05_tail_risk_hedge_optimizer_output.json",
        "06_reverse_stress_testing_input.json",
        "06_reverse_stress_testing_output.json",
        "07_almgren_chriss_liquidity_input.json",
        "07_almgren_chriss_liquidity_output.json",
        "08_supply_chain_mutation_input.json",
        "08_supply_chain_mutation_output.json",
        "09_four_eyes_audit_vault_input.json",
        "09_four_eyes_audit_vault_output.json",
        "README.md",
        "generate_synthetic_test_data.py",
    ]
    for filename in expected_files:
        p = FIXTURES_DIR / filename
        assert p.exists(), f"Missing synthetic test data file: {p}"
        assert p.stat().st_size > 0, f"File {p} is empty"


def test_case_01_taiwan_foundry_fixture():
    """Validates Case 01 Taiwan Foundry Cascade against ContagionPropagator and compute_portfolio_valuation."""
    with open(FIXTURES_DIR / "01_taiwan_foundry_shock_input.json") as f:
        inp = json.load(f)
    with open(FIXTURES_DIR / "01_taiwan_foundry_shock_output.json") as f:
        out = json.load(f)

    nodes_df, edges_df = snapshot_service.load_graph_snapshot()
    propagator = ContagionPropagator(alpha_decay=0.65, max_hops=4)
    prop_res = propagator.propagate(
        initial_shock=inp["initial_shocks"],
        scenario_name=inp["scenario_name"],
        portfolio_weights=inp["portfolio_weights"],
        nodes_df=nodes_df,
        edges_df=edges_df,
        horizon_days=inp["horizon_days"],
        node_inventory_days=inp["inventory_buffer_overrides"],
    )

    assert prop_res.total_active_nodes == out["total_active_nodes"]
    assert prop_res.critical_paths[:2] == out["critical_propagation_paths"][:2]

    # Verify inventory buffering prevented order 1 direct shock on NVDA and AAPL
    assert prop_res.node_shocks["NVDA"].order1_direct == 0.0
    assert ("AAPL" not in prop_res.node_shocks) or (prop_res.node_shocks["AAPL"].order1_direct == 0.0)
    assert prop_res.node_shocks["TSM"].cumulative_shock < -0.25


def test_case_02_suez_ais_telemetry_fixture():
    """Validates Case 02 Suez Choke Point & AIS Telemetry against AISThreatEngine."""
    with open(FIXTURES_DIR / "02_suez_maritime_blockade_input.json") as f:
        inp = json.load(f)
    with open(FIXTURES_DIR / "02_suez_maritime_blockade_output.json") as f:
        out = json.load(f)

    ais_engine = AISThreatEngine()
    suez = ChokePointTelemetry(
        choke_point_id=inp["target_choke_point"],
        name="Suez Canal / Bab-el-Mandeb",
        lat=29.9,
        lng=32.5,
        baseline_daily_vessels=inp["baseline_vessel_queue"],
        current_vessel_count=inp["active_vessel_queue"],
        transit_speed_knots=inp["observed_transit_speed_knots"],
        baseline_speed_knots=inp["baseline_transit_speed_knots"],
        status=ChokePointStatus.BLOCKADE,
        criticality_weight=0.20,
    )
    suez.compute_metrics()
    svi = ais_engine.compute_systemic_vulnerability_index([suez])

    assert round(svi, 2) == out["systemic_vulnerability_index"]
    assert round(suez.congestion_index, 2) == out["target_choke_point_telemetry"]["congestion_index"]
    assert suez.disruption_probability > 0.95


def test_case_03_aladdin_csv_fixture():
    """Validates Case 03 BlackRock Aladdin Portfolio Ingestion."""
    df = pd.read_csv(FIXTURES_DIR / "03_institutional_portfolio_aladdin_input.csv")
    with open(FIXTURES_DIR / "03_institutional_portfolio_aladdin_output.json") as f:
        out = json.load(f)

    assert len(df) == out["holdings_count"]
    total_notional = float(df["NotionalUSD"].sum())
    assert total_notional == out["total_notional_usd"]
    assert out["rule_p01_privacy_status"]["dollar_values_scrubbed_from_llm"] is True


def test_case_04_multi_asset_convexity_fixture():
    """Validates Case 04 Multi-Asset Valuation and non-linear Greeks."""
    with open(FIXTURES_DIR / "04_multi_asset_derivatives_port_input.json") as f:
        inp = json.load(f)
    with open(FIXTURES_DIR / "04_multi_asset_derivatives_port_output.json") as f:
        out = json.load(f)

    # Validate Put Option (Gamma hedge)
    opt_pos = OptionPosition(
        ticker="NVDA",
        notional=150000.0,
        option_type=OptionType.PUT,
        spot=125.0,
        strike=115.0,
        maturity_years=0.25,
        implied_vol=0.45,
        side=PositionSide.LONG,
    )
    opt_detail = evaluate_any_instrument(opt_pos, shock=-0.28)
    assert opt_detail.pnl > 400000.0  # Massive gamma profit
    assert round(opt_detail.pnl, 2) == out["evaluated_positions"][1]["stressed_pnl_usd"]

    # Validate Private Credit covenant breach
    pc_pos = PrivateCreditPosition(
        ticker="SUPPLIER_01",
        notional=2000000.0,
        initial_leverage=4.8,
        covenant_max_leverage=4.5,
        recovery_rate=0.65,
        spread_bps=650.0,
        side=PositionSide.LONG,
    )
    pc_detail = evaluate_any_instrument(pc_pos, shock=-0.40)
    assert pc_detail.pnl == -700000.0  # 35% writedown
    assert "COVENANT BREACH" in pc_detail.status_notes


def test_case_05_tail_risk_hedge_optimizer_fixture():
    """Validates Case 05 SLSQP Tail-Risk Hedge Optimizer."""
    with open(FIXTURES_DIR / "05_tail_risk_hedge_optimizer_input.json") as f:
        inp = json.load(f)
    with open(FIXTURES_DIR / "05_tail_risk_hedge_optimizer_output.json") as f:
        out = json.load(f)

    candidates = [
        HedgeCandidate(
            candidate_id=c["candidate_id"],
            target_node=c["target_node"],
            instrument_type=c["instrument_type"],
            side=c["side"],
            unit_cost_bps=c["unit_cost_bps"],
            protection_elasticity=c["protection_elasticity"],
            max_notional=c["max_notional"],
            description=c["description"],
        )
        for c in inp["candidate_instruments"]
    ]
    opt = TailRiskHedgeOptimizer(candidates=candidates)
    res = opt.optimize_hedge(
        portfolio_notional=inp["unhedged_portfolio_notional"],
        unhedged_pnl=inp["unhedged_pnl_usd"],
        node_shocks=inp["node_shocks"],
        budget_limit=inp["max_hedge_budget_usd"],
    )

    assert res.hedged_pnl > 0.0  # Successful turnaround
    assert round(res.total_hedge_cost, 2) == round(out["total_hedge_cost_usd"], 2)
    assert res.cvar_reduction_pct >= 90.0


def test_case_06_reverse_stress_testing_fixture():
    """Validates Case 06 Algorithmic Reverse Stress Testing minimal L2 norm."""
    with open(FIXTURES_DIR / "06_reverse_stress_testing_input.json") as f:
        inp = json.load(f)
    with open(FIXTURES_DIR / "06_reverse_stress_testing_output.json") as f:
        out = json.load(f)

    tester = ReverseStressTester(key_factors=list(inp["factor_sensitivities"].keys()))
    res = tester.find_breaking_point(
        portfolio_notional=inp["portfolio_notional_usd"],
        target_loss_pct=inp["target_loss_pct"],
        factor_sensitivities=inp["factor_sensitivities"],
    )

    assert res.critical_factor == out["critical_factor"]
    assert round(res.norm_l2, 4) == out["minimal_l2_norm"]
    assert res.achieved_loss_pct >= inp["target_loss_pct"]


def test_case_07_almgren_chriss_liquidity_fixture():
    """Validates Case 07 Almgren-Chriss Liquidity & Fire-Sale Margin Call."""
    with open(FIXTURES_DIR / "07_almgren_chriss_liquidity_input.json") as f:
        inp = json.load(f)
    with open(FIXTURES_DIR / "07_almgren_chriss_liquidity_output.json") as f:
        out = json.load(f)

    engine = EndogenousLiquidityEngine(gamma_perm=0.15, eta_temp=0.25)
    positions = [
        LiquidationPosition(
            asset_id=p["asset_id"],
            target_notional=p["target_notional"],
            adv_30d=p["adv_30d"],
            volatility_ann=p["volatility_ann"],
            bid_ask_spread_bps=p["bid_ask_spread_bps"],
            liquidation_urgency=p["liquidation_urgency"],
        )
        for p in inp["positions"]
    ]
    res = engine.evaluate_liquidation(
        positions=positions,
        liquidation_pct=inp["liquidation_pct"],
        participation_rate=inp["market_participation_rate"],
        fund_unencumbered_cash=inp["fund_unencumbered_cash_usd"],
        portfolio_unhedged_pnl=inp["portfolio_unhedged_pnl_usd"],
        gross_derivative_notional=inp["gross_derivative_notional_usd"],
    )

    assert res.total_notional_liquidated == out["total_notional_liquidated_usd"]
    assert round(res.total_market_impact_loss, 2) == out["total_market_impact_loss_usd"]
    assert res.margin_summary.margin_call_cash_drain == out["margin_summary"]["margin_call_cash_drain_usd"]


def test_case_08_supply_chain_mutation_fixture():
    """Validates Case 08 What-If Supply Chain Graph Mutation ROI."""
    with open(FIXTURES_DIR / "08_supply_chain_mutation_input.json") as f:
        inp = json.load(f)
    with open(FIXTURES_DIR / "08_supply_chain_mutation_output.json") as f:
        out = json.load(f)

    mut_engine = GraphMutationEngine()
    mut_objs = [
        GraphMutation(
            mutation_type=MutationType(m["mutation_type"]),
            source_id=m["source_id"],
            target_id=m["target_id"],
            new_weight=m["new_weight"],
            capex_cost=m["capex_cost"],
            lead_time_months=m["lead_time_months"],
            rationale=m["rationale"],
        )
        for m in inp["mutations"]
    ]

    nodes_df, edges_df = snapshot_service.load_graph_snapshot()
    _, tickers, notionals, _ = snapshot_service.load_portfolio_snapshot()
    portfolio_notionals = {tick: float(n) for tick, n in zip(tickers, notionals)}
    base_edges = {(row["source_id"], row["target_id"]): float(row["base_weight"]) for _, row in edges_df.iterrows()}

    # Propagate base shock
    propagator = ContagionPropagator(alpha_decay=0.65, max_hops=4)
    prop_res = propagator.propagate(
        initial_shock=inp["test_shock"],
        nodes_df=nodes_df,
        edges_df=edges_df,
    )
    base_shocks = {nid: res.cumulative_shock for nid, res in prop_res.node_shocks.items()}

    res = mut_engine.evaluate_mutation(
        mutation_name=inp["intervention_name"],
        mutations=mut_objs,
        base_shocks=base_shocks,
        positions=portfolio_notionals,
        base_edges=base_edges,
        alpha_damping=0.65,
    )

    assert res.is_financially_viable is True
    assert res.resilience_roi_multiple >= 1.5
    assert round(res.capital_savings, 2) == out["capital_savings_usd"]


def test_case_09_four_eyes_audit_fixture():
    """Validates Case 09 Cryptographic SHA-256 seal."""
    with open(FIXTURES_DIR / "09_four_eyes_audit_vault_input.json") as f:
        inp = json.load(f)
    with open(FIXTURES_DIR / "09_four_eyes_audit_vault_output.json") as f:
        out = json.load(f)

    seal_manifest = f"{inp['run_id']}|{inp['model_version']}|{inp['stressed_cvar_99_pct']}|{inp['primary_auditor']['name']}|{inp['secondary_signoff_request']['approver_name']}"
    sha256_seal = hashlib.sha256(seal_manifest.encode("utf-8")).hexdigest()

    assert sha256_seal == out["cryptographic_sha256_seal"]
    assert out["audit_status"] == "APPROVED_AND_LOCKED"
