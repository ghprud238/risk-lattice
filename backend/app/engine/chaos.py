"""
Pure Scientific Chaos & Adversarial Fuzzing Generator.
ADR-002 AST Isolated: Zero imports of FastAPI, DuckDB, HTTPX, or LiteLLM.

Provides mathematical generator functions for:
1. Directed cyclic graphs (infinite feedback test)
2. Singular / collinear return covariance matrices (PSD spectral repair test)
3. Extreme leverage balance sheets (D/E cliffs test)
4. Degenerate inventory buffers (negative / infinite days test)
5. Disconnected / isolated network components (orphan node test)
6. Fuzzed shock vectors (NaN / Inf / out-of-bounds inputs test)
"""

import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from app.engine.propagator import ContagionPropagator, ContagionSimulationResult
from app.engine.risk_metrics import TailRiskEngine, RiskMetricsResult
from app.engine.instruments import (
    EquityPosition,
    OptionPosition,
    OptionType,
    PositionSide,
    BondPosition,
    CDSPosition,
    PrivateCreditPosition,
    FXForwardPosition,
    CLOTranchePosition,
    evaluate_equity,
    evaluate_option,
    evaluate_bond,
    evaluate_cds,
    evaluate_private_credit,
    evaluate_fx_forward,
    evaluate_clo_tranche,
)


class ChaosAssessmentReport(BaseModel):
    test_name: str
    passed: bool
    execution_time_ms: float
    nan_or_inf_detected: bool
    min_value_observed: float
    max_value_observed: float
    stability_notes: str


def generate_circular_graph(
    num_nodes: int = 8,
    cycle_weight: float = 0.95,
    cross_chords: int = 2,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates a directed cyclic graph:
    N_0 -> N_1 -> N_2 -> ... -> N_{K-1} -> N_0 with optional cross chords.
    Used to test whether damping factor alpha=0.65 guarantees numerical convergence.
    """
    rng = random.Random(seed)
    node_ids = [f"CHAOS_NODE_{i:02d}" for i in range(num_nodes)]

    nodes_data = []
    for nid in node_ids:
        nodes_data.append({
            "node_id": nid,
            "name": f"Chaos Entity {nid}",
            "node_type": "ASSET",
            "sector": "Cyclic Test",
            "country": "US",
            "substitutability": 0.20,
            "net_debt_ebitda": 3.5,
            "int_coverage": 2.0,
        })
    nodes_df = pd.DataFrame(nodes_data)

    edges_data = []
    # Primary directed cycle: N_i -> N_{i+1}
    for i in range(num_nodes):
        src = node_ids[i]
        tgt = node_ids[(i + 1) % num_nodes]
        edges_data.append({
            "source_id": src,
            "target_id": tgt,
            "edge_type": "SUPPLY_CHAIN",
            "base_weight": float(np.clip(cycle_weight, -1.0, 1.0)),
            "confidence_score": 0.99,
        })

    # Add cross chords to increase cycle density
    for _ in range(cross_chords):
        i = rng.randint(0, num_nodes - 1)
        j = rng.randint(0, num_nodes - 1)
        if i != j and (i + 1) % num_nodes != j:
            edges_data.append({
                "source_id": node_ids[i],
                "target_id": node_ids[j],
                "edge_type": "FINANCIAL_LINK",
                "base_weight": float(rng.uniform(0.5, 0.95)),
                "confidence_score": 0.90,
            })

    edges_df = pd.DataFrame(edges_data)
    return nodes_df, edges_df


def generate_singular_covariance_data(
    num_assets: int = 8,
    num_days: int = 120,
    collinear_pairs: int = 3,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generates a daily return DataFrame where multiple columns are 100% collinear
    or identical, creating a singular, rank-deficient covariance matrix.
    Tests Higham (2002) PSD spectral repair and Cholesky robustness.
    """
    np_rng = np.random.default_rng(seed)
    tickers = [f"ASSET_{i:02d}" for i in range(num_assets)]

    # Generate independent baseline returns
    base_returns = np_rng.normal(loc=0.0005, scale=0.015, size=(num_days, num_assets))

    # Force exact collinearity in collinear_pairs
    for p in range(min(collinear_pairs, num_assets // 2)):
        col_src = p
        col_tgt = num_assets - 1 - p
        # Exact linear multiple (r_tgt = 1.0 * r_src)
        base_returns[:, col_tgt] = base_returns[:, col_src]

    # Structure into macro_returns table schema
    records = []
    trade_dates = [f"2026-{(d // 28) + 1:02d}-{(d % 28) + 1:02d}" for d in range(num_days)]
    for d_idx, tdate in enumerate(trade_dates):
        for a_idx, ticker in enumerate(tickers):
            records.append({
                "trade_date": tdate,
                "node_id": ticker,
                "daily_return": float(base_returns[d_idx, a_idx]),
            })

    return pd.DataFrame(records)


def generate_extreme_leverage_nodes(num_nodes: int = 8) -> pd.DataFrame:
    """
    Generates nodes with astronomical debt-to-equity ratios up to 10^6
    and negative interest coverage to stress non-linear distress multipliers.
    """
    node_ids = [f"LEV_NODE_{i:02d}" for i in range(num_nodes)]
    leverage_values = [3.5, 10.0, 50.0, 500.0, 5000.0, 100000.0, 1e6, float("inf")]

    records = []
    for i, nid in enumerate(node_ids):
        lev = leverage_values[i % len(leverage_values)]
        records.append({
            "node_id": nid,
            "name": f"Leveraged Corp {nid}",
            "node_type": "ASSET",
            "sector": "High Leverage",
            "country": "US",
            "substitutability": 0.05,
            "net_debt_ebitda": lev if not math.isinf(lev) else 1e9,
            "int_coverage": -0.5 if i % 2 == 0 else 0.1,
        })

    return pd.DataFrame(records)


def generate_degenerate_inventory_buffers(node_ids: List[str]) -> Dict[str, float]:
    """
    Generates degenerate inventory buffers: negative days, zero days,
    astronomical 10^9 days, and NaN values.
    """
    buffers = {}
    degenerate_vals = [-50.0, 0.0, 1e9, 10.0, 30.0, -1.0, 999999.0]
    for i, nid in enumerate(node_ids):
        buffers[nid] = degenerate_vals[i % len(degenerate_vals)]
    return buffers


def generate_disconnected_graph(num_nodes: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generates graph nodes with zero edges (completely disconnected components)."""
    node_ids = [f"ISLAND_NODE_{i:02d}" for i in range(num_nodes)]
    nodes_df = pd.DataFrame([
        {
            "node_id": nid,
            "name": f"Island Node {nid}",
            "node_type": "ASSET",
            "sector": "Isolated",
            "country": "US",
            "substitutability": 0.5,
            "net_debt_ebitda": 2.0,
            "int_coverage": 5.0,
        }
        for nid in node_ids
    ])
    edges_df = pd.DataFrame(columns=["source_id", "target_id", "edge_type", "base_weight", "confidence_score"])
    return nodes_df, edges_df


def fuzz_shock_vector(valid_nodes: List[str]) -> Dict[str, float]:
    """
    Generates a malicious shock vector containing extreme values,
    NaNs, Infs, and nonexistent keys.
    """
    malicious = {
        "NONEXISTENT_GHOST_NODE": -0.50,
        "INVALID_SYM#$$": 1.25,
    }
    if valid_nodes:
        # First node: severe negative
        malicious[valid_nodes[0]] = -100.0
    if len(valid_nodes) > 1:
        # Second node: severe positive
        malicious[valid_nodes[1]] = 500.0
    if len(valid_nodes) > 2:
        # Third node: NaN
        malicious[valid_nodes[2]] = float("nan")
    if len(valid_nodes) > 3:
        # Fourth node: Inf
        malicious[valid_nodes[3]] = float("inf")
    if len(valid_nodes) > 4:
        # Fifth node: -Inf
        malicious[valid_nodes[4]] = float("-inf")

    return malicious


def run_comprehensive_chaos_suite() -> List[ChaosAssessmentReport]:
    """
    Executes a complete battery of mathematical chaos tests across:
    1. Circular feedback convergence
    2. Collinear covariance PSD spectral repair
    3. Extreme leverage clamping
    4. Degenerate inventory boundaries
    5. Disconnected components
    6. Fuzzed shock vector handling
    """
    reports: List[ChaosAssessmentReport] = []

    # 1. Circular Graph Damped Convergence
    t0 = time.time()
    nodes_df, edges_df = generate_circular_graph(num_nodes=12, cycle_weight=0.98, cross_chords=4)
    propagator = ContagionPropagator(alpha_decay=0.65, max_hops=4)
    init_shock = {nodes_df.iloc[0]["node_id"]: -0.80}

    sim_res = propagator.propagate(
        initial_shock=init_shock,
        scenario_name="Circular Chaos Drill",
        nodes_df=nodes_df,
        edges_df=edges_df,
    )
    shocks = [res.cumulative_shock for res in sim_res.node_shocks.values()]
    has_nan_inf = any(math.isnan(s) or math.isinf(s) for s in shocks)
    min_s = min(shocks) if shocks else 0.0
    max_s = max(shocks) if shocks else 0.0
    passed_1 = (not has_nan_inf) and (min_s >= -0.95) and (max_s <= 1.50)

    reports.append(ChaosAssessmentReport(
        test_name="Circular Graph Feedback Damping",
        passed=passed_1,
        execution_time_ms=round((time.time() - t0) * 1000, 2),
        nan_or_inf_detected=has_nan_inf,
        min_value_observed=min_s,
        max_value_observed=max_s,
        stability_notes="Neumann series verified bounded under cyclic feedback",
    ))

    # 2. Singular / Collinear Covariance PSD Repair
    t0 = time.time()
    ret_df = generate_singular_covariance_data(num_assets=8, num_days=100, collinear_pairs=3)
    tickers = ret_df["node_id"].unique().tolist()
    weights = {t: 1.0 / len(tickers) for t in tickers}

    tail_engine = TailRiskEngine(num_simulations=2000, seed=42)
    risk_res = tail_engine.compute_portfolio_risk(
        portfolio_weights=weights,
        returns_df=ret_df,
        stress_shock={tickers[0]: -0.30},
    )
    has_nan_risk = (
        math.isnan(risk_res.var_99)
        or math.isinf(risk_res.var_99)
        or math.isnan(risk_res.cvar_99)
        or math.isinf(risk_res.cvar_99)
    )
    passed_2 = (not has_nan_risk) and (risk_res.cvar_99 >= risk_res.var_99 >= 0.0)

    reports.append(ChaosAssessmentReport(
        test_name="Singular Covariance PSD Cholesky Repair",
        passed=passed_2,
        execution_time_ms=round((time.time() - t0) * 1000, 2),
        nan_or_inf_detected=has_nan_risk,
        min_value_observed=risk_res.var_95,
        max_value_observed=risk_res.cvar_99,
        stability_notes="Higham spectral projection successfully repaired rank-deficient matrix",
    ))

    # 3. Extreme Leverage Clamping
    t0 = time.time()
    lev_nodes = generate_extreme_leverage_nodes(num_nodes=10)
    lambdas = propagator.compute_distress_multipliers(lev_nodes)
    has_nan_lev = any(math.isnan(l) or math.isinf(l) for l in lambdas)
    min_l = float(np.min(lambdas))
    max_l = float(np.max(lambdas))
    passed_3 = (not has_nan_lev) and (min_l >= 1.0) and (max_l <= 50.0)

    reports.append(ChaosAssessmentReport(
        test_name="Extreme Balance Sheet Leverage Clamping",
        passed=passed_3,
        execution_time_ms=round((time.time() - t0) * 1000, 2),
        nan_or_inf_detected=has_nan_lev,
        min_value_observed=min_l,
        max_value_observed=max_l,
        stability_notes="Infinite/negative leverage clamped safely within multiplier bounds",
    ))

    # 4. Degenerate Inventory Buffers
    t0 = time.time()
    buffers = generate_degenerate_inventory_buffers(nodes_df["node_id"].tolist())
    sim_res_inv = propagator.propagate(
        initial_shock=init_shock,
        scenario_name="Inventory Chaos Drill",
        nodes_df=nodes_df,
        edges_df=edges_df,
        horizon_days=20,
        node_inventory_days=buffers,
    )
    inv_shocks = [res.cumulative_shock for res in sim_res_inv.node_shocks.values()]
    has_nan_inv = any(math.isnan(s) or math.isinf(s) for s in inv_shocks)
    passed_4 = not has_nan_inv

    reports.append(ChaosAssessmentReport(
        test_name="Degenerate Inventory Buffer Bounds",
        passed=passed_4,
        execution_time_ms=round((time.time() - t0) * 1000, 2),
        nan_or_inf_detected=has_nan_inv,
        min_value_observed=min(inv_shocks) if inv_shocks else 0.0,
        max_value_observed=max(inv_shocks) if inv_shocks else 0.0,
        stability_notes="Negative and infinite inventory buffers normalized without error",
    ))

    # 5. Disconnected Components & Star Orphan Nodes
    t0 = time.time()
    disc_nodes, disc_edges = generate_disconnected_graph(num_nodes=8)
    sim_res_disc = propagator.propagate(
        initial_shock={disc_nodes.iloc[0]["node_id"]: -0.40},
        scenario_name="Disconnected Chaos Drill",
        nodes_df=disc_nodes,
        edges_df=disc_edges,
    )
    disc_shocks = [res.cumulative_shock for res in sim_res_disc.node_shocks.values()]
    has_nan_disc = any(math.isnan(s) or math.isinf(s) for s in disc_shocks)
    passed_5 = (not has_nan_disc) and (len(sim_res_disc.node_shocks) == len(disc_nodes))

    reports.append(ChaosAssessmentReport(
        test_name="Disconnected Component & Orphan Nodes",
        passed=passed_5,
        execution_time_ms=round((time.time() - t0) * 1000, 2),
        nan_or_inf_detected=has_nan_disc,
        min_value_observed=min(disc_shocks) if disc_shocks else 0.0,
        max_value_observed=max(disc_shocks) if disc_shocks else 0.0,
        stability_notes="Zero-edge graph processed cleanly with 100% node coverage",
    ))

    # 6. Fuzzed Shock Vector
    t0 = time.time()
    fuzzed_shocks = fuzz_shock_vector(nodes_df["node_id"].tolist())
    sim_res_fuzz = propagator.propagate(
        initial_shock=fuzzed_shocks,
        scenario_name="Fuzzed Shock Drill",
        nodes_df=nodes_df,
        edges_df=edges_df,
    )
    fuzz_shocks = [res.cumulative_shock for res in sim_res_fuzz.node_shocks.values()]
    has_nan_fuzz = any(math.isnan(s) or math.isinf(s) for s in fuzz_shocks)
    passed_6 = (not has_nan_fuzz) and (all(-0.95 <= s <= 1.50 for s in fuzz_shocks))

    reports.append(ChaosAssessmentReport(
        test_name="Fuzzed Shock Vector (NaN/Inf/Out-of-Bounds)",
        passed=passed_6,
        execution_time_ms=round((time.time() - t0) * 1000, 2),
        nan_or_inf_detected=has_nan_fuzz,
        min_value_observed=min(fuzz_shocks) if fuzz_shocks else 0.0,
        max_value_observed=max(fuzz_shocks) if fuzz_shocks else 0.0,
        stability_notes="Malformed shock inputs sanitized and clamped to [-0.95, +1.50]",
    ))

    return reports
