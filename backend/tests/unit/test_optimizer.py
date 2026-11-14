"""Unit tests for Tail-Risk Hedge Optimizer & Reverse Stress Tester.
PRD Section 16 & Section 24.1 compliant:
- Zero external network, database, or LLM mocks required.
- Pure scientific computing verification of SLSQP optimization and inverse shock search.
"""

import pytest
import numpy as np

from app.engine.optimizer import (
    HedgeCandidate,
    ReverseStressTester,
    TailRiskHedgeOptimizer,
)


def test_hedge_optimizer_allocation_within_budget():
    """Verifies that optimal hedge allocation stays strictly within the specified dollar budget."""
    optimizer = TailRiskHedgeOptimizer()

    unhedged_pnl = -20_000_000.0
    budget = 400_000.0
    node_shocks = {
        "TSM": -0.35,
        "NVDA": -0.30,
        "F": -0.25,
    }

    result = optimizer.optimize_hedge(
        portfolio_notional=100_000_000.0,
        unhedged_pnl=unhedged_pnl,
        node_shocks=node_shocks,
        budget_limit=budget,
    )

    # Assert budget constraint satisfied
    assert result.total_hedge_cost <= budget + 1e-4
    assert result.total_hedge_cost > 0.0

    # Assert net PnL and CVaR improvement
    assert result.hedged_pnl > unhedged_pnl
    assert result.pnl_improvement > 0.0
    assert result.hedged_cvar_99 < result.initial_cvar_99
    assert result.cvar_reduction_pct > 0.0

    # Assert recommendations generated
    assert len(result.recommendations) > 0
    for rec in result.recommendations:
        assert rec.allocated_notional > 0
        assert rec.estimated_cost > 0
        assert rec.pnl_protection > 0

    # Assert efficient frontier monotonicity
    assert len(result.efficient_frontier) == 5
    for i in range(len(result.efficient_frontier) - 1):
        assert result.efficient_frontier[i]["budget"] <= result.efficient_frontier[i + 1]["budget"]


def test_hedge_optimizer_zero_shock_zero_allocation():
    """Verifies that if there are no negative shocks, optimizer does not allocate wasteful protection."""
    optimizer = TailRiskHedgeOptimizer()
    node_shocks = {"TSM": 0.05, "NVDA": 0.10}

    result = optimizer.optimize_hedge(
        portfolio_notional=100_000_000.0,
        unhedged_pnl=5_000_000.0,
        node_shocks=node_shocks,
        budget_limit=200_000.0,
    )

    # Unit protection is 0 for positive shocks, so cost should be 0
    assert result.total_hedge_cost == 0.0
    assert len(result.recommendations) == 0


def test_reverse_stress_tester_finds_minimal_breaking_point():
    """Verifies that reverse stress testing converges to the target portfolio drawdown."""
    tester = ReverseStressTester(
        key_factors=["FOUNDRY_TW", "BALTIC_DRY", "BRENT_CRUDE", "SOFR_SPREAD"]
    )

    target_loss = 0.25  # 25% target portfolio drawdown
    sensitivities = {
        "FOUNDRY_TW": 0.50,
        "BALTIC_DRY": 0.30,
        "BRENT_CRUDE": 0.20,
        "SOFR_SPREAD": 0.40,
    }

    result = tester.find_breaking_point(
        portfolio_notional=100_000_000.0,
        target_loss_pct=target_loss,
        factor_sensitivities=sensitivities,
    )

    # Assert achieved loss reaches target (within solver numerical tolerance)
    assert result.achieved_loss_pct >= target_loss - 1e-3
    assert result.norm_l2 > 0.0

    # Assert all shocks are negative (or zero)
    for factor, shock in result.minimal_shocks.items():
        assert shock <= 0.0
        assert abs(shock) <= 0.85

    # Assert critical factor identified
    assert result.critical_factor in sensitivities
    assert len(result.top_vulnerable_nodes) > 0
    assert result.iterations > 0
