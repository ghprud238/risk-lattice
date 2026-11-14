"""Unit tests for Multi-Period Timeline Simulation & Scenario Diffing Engines.
PRD Section 16 & Section 24.1 compliant:
- Pure mathematical tests without external network or DB calls.
"""

import pytest

from app.engine.diffing import NodeDiffStatus, ScenarioDiffEngine
from app.engine.timeline import MultiPeriodTimelineEngine


def test_multi_period_timeline_progression():
    """Verifies wave-by-wave shock propagation and inventory buffer exhaustion over 90 days."""
    engine = MultiPeriodTimelineEngine()

    initial_shocks = {"TSM": -0.40}
    horizons = [0, 7, 14, 30, 45, 60, 90]

    result = engine.simulate(
        initial_shocks=initial_shocks,
        portfolio_notional=100_000_000.0,
        time_horizon_days=horizons,
    )

    assert len(result.steps) == len(horizons)
    assert result.peak_drawdown_pnl < 0.0
    assert result.peak_drawdown_pct < 0.0
    assert result.total_milestones > 0

    # Step 0: only TSM is shocked, downstream not reached yet
    step_0 = result.steps[0]
    assert step_0.day == 0
    assert step_0.node_shocks["TSM"] <= -0.40
    assert any(m.event_type == "SHOCK_TRIGGER" for m in step_0.milestones)

    # Step 14: TSM 14-day safety inventory exhausts
    step_14 = next(s for s in result.steps if s.day == 14)
    assert step_14.inventory_levels["TSM"] == 0.0

    # Step 90: Downstream nodes NVDA and AAPL have been infected
    step_90 = result.steps[-1]
    assert step_90.node_shocks.get("NVDA", 0.0) < 0.0
    assert step_90.node_shocks.get("AAPL", 0.0) < 0.0


def test_scenario_diffing_engine():
    """Verifies comparative attribution between baseline and mitigated scenarios."""
    diff_engine = ScenarioDiffEngine()

    shocks_a = {
        "TSM": -0.40,
        "NVDA": -0.35,
        "AAPL": -0.25,
        "F": -0.20,
    }
    # Scenario B has hedged/mitigated TSM and NVDA, but worsened F
    shocks_b = {
        "TSM": -0.15,   # De-risked (-62.5%)
        "NVDA": -0.10,  # De-risked (-71.4%)
        "AAPL": -0.24,  # Unchanged (-4%)
        "F": -0.32,     # Amplified (+60%)
    }
    positions = {
        "TSM": 20_000_000.0,
        "NVDA": 25_000_000.0,
        "AAPL": 20_000_000.0,
        "F": 10_000_000.0,
    }

    result = diff_engine.diff_scenarios(
        scenario_a_name="Unmitigated Blockade",
        scenario_b_name="Dual-Sourced Re-routing",
        shocks_a=shocks_a,
        shocks_b=shocks_b,
        positions=positions,
    )

    # Assert PnL improvement
    assert result.pnl_b > result.pnl_a
    assert result.delta_pnl > 0.0
    assert result.delta_cvar_99 < 0.0
    assert result.net_improvement_pct > 0.0

    # Assert status classification
    status_map = {d.node_id: d.status for d in result.node_diffs}
    assert status_map["TSM"] == NodeDiffStatus.DE_RISKED
    assert status_map["NVDA"] == NodeDiffStatus.DE_RISKED
    assert status_map["AAPL"] == NodeDiffStatus.UNCHANGED
    assert status_map["F"] == NodeDiffStatus.AMPLIFIED

    assert result.de_risked_nodes_count >= 2
    assert result.amplified_nodes_count >= 1
    assert len(result.top_de_risked_nodes) >= 2
