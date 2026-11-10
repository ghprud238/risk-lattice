"""
Performance Gate Verification for Milestone 4:
Asserts 50-node multi-hop propagation + Student-t copula runs in < 2.0 seconds.
"""
import time
import pytest
from app.engine.propagator import ContagionPropagator
from app.engine.risk_metrics import TailRiskEngine


def test_simulation_latency_under_2_seconds():
    from app.db.database import db_manager
    from app.services.snapshot_service import snapshot_service

    nodes_df, edges_df = snapshot_service.load_graph_snapshot()
    propagator = ContagionPropagator()
    risk_engine = TailRiskEngine(df_t=4.0, num_simulations=2000, seed=42)

    t0 = time.perf_counter()

    # 1. Multi-hop propagation on 50-node graph
    sim_result = propagator.propagate(
        initial_shock={"FOUNDRY_TW": -0.70, "BALTIC_DRY": 1.80, "US10Y_REAL": 0.02},
        scenario_name="Taiwan & Rate Shock",
        nodes_df=nodes_df,
        edges_df=edges_df,
    )

    # 2. Risk metrics
    risk_res = risk_engine.compute_portfolio_risk(
        portfolio_weights={"NVDA": 0.25, "TSLA": 0.25, "F": 0.25, "DAL": 0.25},
        stress_shock={nid: res.cumulative_shock for nid, res in sim_result.node_shocks.items()},
        db=db_manager,
    )

    elapsed = time.perf_counter() - t0

    print(f"\n[Milestone 4 Performance Gate] 50-node propagation + 2,000-path Copula took: {elapsed:.3f}s")
    assert elapsed < 2.0, f"Execution latency exceeded 2.0s: {elapsed:.3f}s"
    assert sim_result.total_active_nodes >= 20
    assert risk_res.cvar_99 > 0
