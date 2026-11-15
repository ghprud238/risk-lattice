"""Unit tests for Endogenous Market Impact & What-If Graph Mutation Engines.
PRD Section 16 & Section 24.1 compliant:
- Pure mathematical tests without external network or DB calls.
"""

import pytest

from app.engine.liquidity import (
    EndogenousLiquidityEngine,
    LiquidationPosition,
)
from app.engine.mutation import (
    GraphMutation,
    GraphMutationEngine,
    MutationType,
)


def test_almgren_chriss_liquidation_and_margin_spiral():
    """Verifies market impact, temporary/permanent slippage, and ISDA margin cash drain."""
    engine = EndogenousLiquidityEngine()

    positions = [
        LiquidationPosition(
            asset_id="NVDA",
            target_notional=20_000_000.0,
            adv_30d=100_000_000.0,
            volatility_ann=0.45,
            bid_ask_spread_bps=3.0,
            liquidation_urgency="HIGH",
        ),
        LiquidationPosition(
            asset_id="F",
            target_notional=10_000_000.0,
            adv_30d=25_000_000.0,
            volatility_ann=0.35,
            bid_ask_spread_bps=5.0,
            liquidation_urgency="FIRE_SALE",
        ),
    ]

    result = engine.evaluate_liquidation(
        positions=positions,
        liquidation_pct=0.25,
        participation_rate=0.10,
        fund_unencumbered_cash=12_000_000.0,
        portfolio_unhedged_pnl=-18_000_000.0,
        gross_derivative_notional=40_000_000.0,
    )

    # 1. Assert liquidation volume
    assert result.total_notional_liquidated == 7_500_000.0
    assert result.total_market_impact_loss > 0.0
    assert result.blended_price_discount_pct > 0.0

    # 2. Assert asset-level impact metrics
    nvda_impact = next(i for i in result.asset_impacts if i.asset_id == "NVDA")
    f_impact = next(i for i in result.asset_impacts if i.asset_id == "F")

    assert nvda_impact.temporary_impact_bps > 0
    assert nvda_impact.permanent_impact_bps > 0
    # F was in FIRE_SALE with higher adv_ratio, so discount should be higher
    assert f_impact.realized_price_discount_pct > nvda_impact.realized_price_discount_pct

    # 3. Assert Margin Call Summary
    assert result.margin_summary.margin_call_cash_drain > 0.0
    assert result.margin_summary.stressed_margin_requirement > result.margin_summary.initial_margin_requirement
    assert result.margin_summary.liquidity_coverage_ratio_post_stress > 0.0
    assert result.fire_sale_contagion_multiplier >= 1.0


def test_what_if_graph_mutation_resilience_roi():
    """Verifies that severing or re-weighting vulnerable edges reduces portfolio loss and yields positive ROI."""
    mutation_engine = GraphMutationEngine()

    base_shocks = {"TSM": -0.40, "NVDA": -0.35, "AAPL": -0.28, "F": -0.20}
    positions = {"TSM": 20_000_000.0, "NVDA": 25_000_000.0, "AAPL": 20_000_000.0, "F": 10_000_000.0}
    base_edges = {("TSM", "NVDA"): 0.38, ("TSM", "AAPL"): 0.34, ("F", "APTV"): 0.30}

    mutations = [
        GraphMutation(
            mutation_type=MutationType.REWEIGHT_EDGE,
            source_id="TSM",
            target_id="NVDA",
            new_weight=0.10,
            capex_cost=1_500_000.0,
            lead_time_months=9,
            rationale="Re-route packaging to TSMC Fab 21 Arizona",
        ),
        GraphMutation(
            mutation_type=MutationType.SEVER_EDGE,
            source_id="TSM",
            target_id="AAPL",
            new_weight=0.0,
            capex_cost=2_000_000.0,
            lead_time_months=12,
            rationale="Dual-source custom silicon",
        ),
    ]

    result = mutation_engine.evaluate_mutation(
        mutation_name="Silicon Supply Decoupling",
        mutations=mutations,
        base_shocks=base_shocks,
        positions=positions,
        base_edges=base_edges,
    )

    # 1. Assert capital savings
    assert result.capital_savings > 0.0
    assert result.mutated_pnl > result.initial_pnl
    assert result.cvar_relief_pct > 0.0

    # 2. Assert financial viability & ROI
    assert result.total_capex == 3_500_000.0
    assert result.resilience_roi_multiple > 0.0
    assert len(result.top_mitigated_nodes) > 0
