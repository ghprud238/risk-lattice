"""Unit tests for Inventory Buffer and Disruption Horizon Dynamics in Contagion Propagation.
Validates:
1. Complete inventory absorption (inv_days >= horizon_days -> zero shock transmitted)
2. Partial inventory absorption (inv_days < horizon_days -> proportional mitigation)
3. Zero inventory just-in-time propagation (inv_days = 0 -> 100% transmitted)
4. Bit-exact analytical kernel verification with inventory buffers
"""

import numpy as np
import pandas as pd
import pytest

from app.engine.propagator import ContagionPropagator, propagate_kernel


def test_complete_inventory_absorption():
    """Validates that safety stock buffer >= disruption duration completely absorbs the shock."""
    # 2-node graph: Node 0 (Supplier TSM) -> Node 1 (Customer AAPL, SUPPLY edge)
    nodes_df = pd.DataFrame([
        {"node_id": "TSM", "node_type": "SUPPLIER", "name": "TSMC", "sector": "Semiconductors", "substitutability": 0.0, "net_debt_ebitda": 0.5, "int_coverage": 10.0, "inventory_days": 0.0},
        {"node_id": "AAPL", "node_type": "ASSET", "name": "Apple", "sector": "Technology", "substitutability": 0.0, "net_debt_ebitda": 1.0, "int_coverage": 8.0, "inventory_days": 45.0},
    ])
    edges_df = pd.DataFrame([
        {"source_id": "TSM", "target_id": "AAPL", "base_weight": 0.80, "weight": 0.80, "edge_type": "SUPPLY"},
    ])

    propagator = ContagionPropagator(alpha_decay=0.65, max_hops=4)

    # 30-day disruption, but Apple has 45 days of inventory buffer!
    result = propagator.propagate(
        initial_shock={"TSM": -0.30},
        scenario_name="30-Day Disruption with 45-Day Buffer",
        nodes_df=nodes_df,
        edges_df=edges_df,
        horizon_days=30,
        node_inventory_days={"AAPL": 45.0},
    )

    # TSM takes the initial shock
    assert result.node_shocks["TSM"].cumulative_shock == pytest.approx(-0.30)
    # AAPL is completely shielded by its 45-day inventory buffer!
    assert result.node_shocks["AAPL"].cumulative_shock == pytest.approx(0.0)
    assert result.node_shocks["AAPL"].hop1 == pytest.approx(0.0)


def test_partial_inventory_absorption():
    """Validates that buffer < horizon attenuates the shock proportionally."""
    nodes_df = pd.DataFrame([
        {"node_id": "TSM", "node_type": "SUPPLIER", "name": "TSMC", "sector": "Semiconductors", "substitutability": 0.0, "net_debt_ebitda": 0.5, "int_coverage": 10.0, "inventory_days": 0.0},
        {"node_id": "F", "node_type": "ASSET", "name": "Ford", "sector": "Automotive", "substitutability": 0.0, "net_debt_ebitda": 2.0, "int_coverage": 4.0, "inventory_days": 10.0},
    ])
    edges_df = pd.DataFrame([
        {"source_id": "TSM", "target_id": "F", "base_weight": 0.50, "weight": 0.50, "edge_type": "SUPPLY"},
    ])

    propagator = ContagionPropagator(alpha_decay=0.65, max_hops=4)

    # Baseline with 0 inventory
    res_no_buffer = propagator.propagate(
        initial_shock={"TSM": -0.40},
        nodes_df=nodes_df,
        edges_df=edges_df,
        horizon_days=20,
        node_inventory_days={"F": 0.0},
    )
    raw_ford_shock = res_no_buffer.node_shocks["F"].cumulative_shock
    assert raw_ford_shock < 0.0

    # With 10 days inventory out of 20 days disruption -> 50% mitigation
    res_with_buffer = propagator.propagate(
        initial_shock={"TSM": -0.40},
        nodes_df=nodes_df,
        edges_df=edges_df,
        horizon_days=20,
        node_inventory_days={"F": 10.0},
    )
    buffered_ford_shock = res_with_buffer.node_shocks["F"].cumulative_shock

    # Buffered shock should be exactly 50% of the raw shock!
    assert buffered_ford_shock == pytest.approx(raw_ford_shock * 0.50, rel=1e-3)


def test_propagate_kernel_with_inventory_buffers():
    """Validates the pure analytical kernel with inventory buffers."""
    # Node 0 (Supplier) -> Node 1 (Buffer 30d) and Node 2 (Buffer 0d)
    seed = np.array([-0.50, 0.0, 0.0], dtype=np.float64)
    edges = [
        (0, 1, 0.80, "SUPPLY"),
        (0, 2, 0.80, "SUPPLY"),
    ]
    # 20-day horizon: Node 1 has 30 days buffer (absorbs 100%), Node 2 has 0 buffer (absorbs 0%)
    inventory_buffers = np.array([0.0, 30.0, 0.0], dtype=np.float64)

    hops, final_total, _, _ = propagate_kernel(
        seed=seed,
        edges=edges,
        alpha=0.65,
        max_hops=2,
        inventory_buffers=inventory_buffers,
        horizon_days=20.0,
    )

    # Node 0 has seed shock -0.50
    assert final_total[0] == pytest.approx(-0.50)
    # Node 1 is shielded by 30-day buffer -> 0.0 impulse
    assert final_total[1] == pytest.approx(0.0)
    # Node 2 receives full unmitigated hop: 0.65 * 0.80 * -0.50 = -0.26
    assert hops[1, 2] == pytest.approx(-0.26)
    assert final_total[2] == pytest.approx(-0.26)
