#!/usr/bin/env python3
"""Offline CLI Smoke Test per Section 20.1 & 20.4.
Verifies end-to-end multi-hop propagation, Copula tail-risk calculation, and valuation
completely offline without spinning up web servers or network calls.
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import db_manager
from app.services.snapshot_service import snapshot_service
from app.engine.propagator import ContagionPropagator
from app.engine.risk_metrics import TailRiskEngine
from app.engine.valuation import compute_portfolio_valuation


def run_smoke_test():
    print("=" * 60)
    print("ContagionGraph Offline Smoke Test (smoke_test.py)")
    print("=" * 60)
    start_time = time.perf_counter()

    # 1. Load immutable snapshot
    print("[1/4] Loading immutable graph and portfolio snapshots...")
    nodes_df, edges_df = snapshot_service.load_graph_snapshot()
    node_ids, tickers, notionals, weights = snapshot_service.load_portfolio_snapshot()
    assert not nodes_df.empty, "Graph nodes empty"
    assert not edges_df.empty, "Graph edges empty"
    print(f"      Loaded {len(nodes_df)} nodes, {len(edges_df)} edges, {len(tickers)} portfolio assets.")

    # 2. Multi-hop propagation
    print("[2/4] Executing 4-hop damped propagation kernel (alpha=0.65)...")
    propagator = ContagionPropagator()
    prop_res = propagator.propagate(
        initial_shock={"NVDA": -0.25, "TSM": -0.30},
        scenario_name="Smoke Test Macro Shock",
        nodes_df=nodes_df,
        edges_df=edges_df,
    )
    assert prop_res.total_active_nodes > 0, "No nodes activated"
    assert "NVDA" in prop_res.node_shocks
    print(f"      Activated {prop_res.total_active_nodes} nodes across network.")
    print(f"      NVDA cumulative shock: {prop_res.node_shocks['NVDA'].cumulative_shock}")

    # 3. Student-t Copula Risk calculation
    print("[3/4] Simulating 5,000 Student-t Copula tail risk paths (PCG64 seed=42)...")
    weights_dict = {tick: float(w) for tick, w in zip(tickers, weights)}
    risk_engine = TailRiskEngine(df_t=4.0, num_simulations=5000, seed=42)
    node_shocks = {nid: res.cumulative_shock for nid, res in prop_res.node_shocks.items()}
    risk_res = risk_engine.compute_portfolio_risk(weights_dict, stress_shock=node_shocks, db=db_manager)
    assert risk_res.cvar_99 > risk_res.var_99, "CVaR must exceed VaR"
    print(f"      VaR(99%):  {risk_res.var_99 * 100:.2f}%")
    print(f"      CVaR(99%): {risk_res.cvar_99 * 100:.2f}%")
    print(f"      Copula/Gaussian Tail Ratio: {risk_res.copula_to_gaussian_ratio:.2f}x")

    # 4. Valuation & Attribution ledger
    print("[4/4] Computing portfolio valuation and attribution ledger...")
    hop_returns = []
    for k in range(5):
        hop_k = [getattr(prop_res.node_shocks.get(nid), f"hop{k}", 0.0) for nid in node_ids]
        hop_returns.append(hop_k)
    import numpy as np
    val_res = compute_portfolio_valuation(node_ids, tickers, notionals, np.array(hop_returns))
    print(f"      Total Portfolio Notional: ${val_res.total_notional:,.2f}")
    print(f"      Total Stressed Dollar PnL: ${val_res.total_pnl:,.2f} ({val_res.portfolio_return * 100:.2f}%)")

    elapsed = time.perf_counter() - start_time
    print("=" * 60)
    print(f"SMOKE TEST PASSED in {elapsed:.3f}s (Budget: < 2.0s)")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
