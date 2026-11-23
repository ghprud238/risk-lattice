"""
Adversarial Chaos Fuzzing & Resilience Test Suite.
Tests:
1. Directed cyclic graphs with high edge weights (feedback loop damping test)
2. Singular / collinear return covariance matrices (PSD spectral repair & Cholesky test)
3. Extreme balance sheet leverage cliffs (D/E up to 10^6 and negative coverage)
4. Degenerate inventory buffers (negative days, infinite buffers, zero duration)
5. Disconnected components and orphan nodes (zero edge graph test)
6. Fuzzed shock vectors (NaN, Inf, out-of-bounds, nonexistent tickers)
7. Circuit breaker state machine (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
8. Circuit breaker fail-open under simulated upstream LLM outage
9. End-to-end chaos suite verification (run_comprehensive_chaos_suite)
"""

import math
import time
import pytest
import numpy as np
import pandas as pd

from app.engine.chaos import (
    generate_circular_graph,
    generate_singular_covariance_data,
    generate_extreme_leverage_nodes,
    generate_degenerate_inventory_buffers,
    generate_disconnected_graph,
    fuzz_shock_vector,
    run_comprehensive_chaos_suite,
)
from app.engine.propagator import ContagionPropagator
from app.engine.risk_metrics import TailRiskEngine
from app.services.circuit_breaker_service import CircuitBreakerService, CircuitState
from app.agents.shock_translator import ShockTranslator, ShockTranslationResponse


def test_circular_graph_feedback_damping():
    """Verifies that dense circular graph feedback loops converge cleanly without numerical explosion."""
    nodes_df, edges_df = generate_circular_graph(num_nodes=10, cycle_weight=0.99, cross_chords=4, seed=123)
    propagator = ContagionPropagator(alpha_decay=0.65, max_hops=4)

    # Initial shock on the entry node
    sim_res = propagator.propagate(
        initial_shock={nodes_df.iloc[0]["node_id"]: -0.85},
        scenario_name="Circular Chaos Feedback",
        nodes_df=nodes_df,
        edges_df=edges_df,
    )

    shocks = [res.cumulative_shock for res in sim_res.node_shocks.values()]
    assert len(shocks) == 10
    assert not any(math.isnan(s) or math.isinf(s) for s in shocks), "NaN or Inf detected in cyclic cascade"
    assert all(-0.95 <= s <= 1.50 for s in shocks), "Cumulative shocks breached [-0.95, +1.50] boundary"


def test_singular_covariance_psd_cholesky_repair():
    """Verifies that 100% collinear return series with rank deficiency do not crash Cholesky decomposition."""
    ret_df = generate_singular_covariance_data(num_assets=8, num_days=120, collinear_pairs=3, seed=42)
    tickers = ret_df["node_id"].unique().tolist()
    weights = {t: 1.0 / len(tickers) for t in tickers}

    engine = TailRiskEngine(num_simulations=1500, seed=42)
    risk_res = engine.compute_portfolio_risk(
        portfolio_weights=weights,
        returns_df=ret_df,
        stress_shock={tickers[0]: -0.25},
    )

    assert not math.isnan(risk_res.var_99)
    assert not math.isinf(risk_res.var_99)
    assert not math.isnan(risk_res.cvar_99)
    assert not math.isinf(risk_res.cvar_99)
    assert risk_res.cvar_99 >= risk_res.var_99 >= 0.0


def test_extreme_leverage_cliff_clamping():
    """Verifies that astronomical leverage (D/E up to 10^6 or inf) clamps safely within distress limits."""
    lev_nodes = generate_extreme_leverage_nodes(num_nodes=10)
    propagator = ContagionPropagator()
    lambdas = propagator.compute_distress_multipliers(lev_nodes)

    assert not any(math.isnan(l) or math.isinf(l) for l in lambdas)
    assert all(1.0 <= l <= 50.0 for l in lambdas), f"Distress multipliers outside [1.0, 50.0]: {lambdas}"


def test_degenerate_inventory_buffers():
    """Verifies that negative or infinite inventory buffers do not raise exceptions or produce NaNs."""
    nodes_df, edges_df = generate_circular_graph(num_nodes=6, cycle_weight=0.7)
    propagator = ContagionPropagator()
    node_ids = nodes_df["node_id"].tolist()
    buffers = generate_degenerate_inventory_buffers(node_ids)

    sim_res = propagator.propagate(
        initial_shock={node_ids[0]: -0.50},
        scenario_name="Degenerate Inventory",
        nodes_df=nodes_df,
        edges_df=edges_df,
        horizon_days=20,
        node_inventory_days=buffers,
    )

    shocks = [res.cumulative_shock for res in sim_res.node_shocks.values()]
    assert not any(math.isnan(s) or math.isinf(s) for s in shocks)


def test_disconnected_graph_propagation():
    """Verifies that an edge-free disconnected graph processes all nodes without error."""
    disc_nodes, disc_edges = generate_disconnected_graph(num_nodes=12)
    propagator = ContagionPropagator()

    sim_res = propagator.propagate(
        initial_shock={disc_nodes.iloc[0]["node_id"]: -0.40},
        scenario_name="Disconnected Graph",
        nodes_df=disc_nodes,
        edges_df=disc_edges,
    )

    assert len(sim_res.node_shocks) == 12
    # Only the shocked node should have non-zero shock
    shocked_id = disc_nodes.iloc[0]["node_id"]
    for nid, res in sim_res.node_shocks.items():
        if nid == shocked_id:
            assert abs(res.cumulative_shock - (-0.40)) < 1e-4
        else:
            assert abs(res.cumulative_shock) < 1e-4


def test_fuzzed_shock_vector_sanitization():
    """Verifies that malicious shock values (NaN, Inf, -100.0, +500.0) are safely clamped."""
    nodes_df, edges_df = generate_circular_graph(num_nodes=8)
    propagator = ContagionPropagator()
    fuzzed = fuzz_shock_vector(nodes_df["node_id"].tolist())

    sim_res = propagator.propagate(
        initial_shock=fuzzed,
        scenario_name="Fuzzed Vector Drill",
        nodes_df=nodes_df,
        edges_df=edges_df,
    )

    shocks = [res.cumulative_shock for res in sim_res.node_shocks.values()]
    assert not any(math.isnan(s) or math.isinf(s) for s in shocks)
    assert all(-0.95 <= s <= 1.50 for s in shocks)


def test_circuit_breaker_lifecycle():
    """Tests full Circuit Breaker state transitions: CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
    cb = CircuitBreakerService(
        name="test_cb",
        failure_threshold=2,
        recovery_timeout=0.1,  # Fast timeout for test
        success_threshold=2,
    )
    assert cb.state == CircuitState.CLOSED

    # Failure 1
    cb.record_failure(ValueError("Simulated timeout 1"))
    assert cb.state == CircuitState.CLOSED

    # Failure 2 -> Trips to OPEN
    cb.record_failure(ValueError("Simulated timeout 2"))
    assert cb.state == CircuitState.OPEN

    # In OPEN: call fast-fails directly to fallback
    def failing_upstream():
        raise RuntimeError("Should not be called while OPEN")

    fallback_called = False
    def fallback_func():
        nonlocal fallback_called
        fallback_called = True
        return "FALLBACK_SUCCESS"

    result = cb.call(failing_upstream, fallback=fallback_func)
    assert result == "FALLBACK_SUCCESS"
    assert fallback_called is True

    # Wait for recovery timeout (0.1s)
    time.sleep(0.12)
    # Checking state should now transition to HALF_OPEN
    assert cb.state == CircuitState.HALF_OPEN

    # Trial call 1 succeeds
    cb.record_success()
    assert cb.state == CircuitState.HALF_OPEN

    # Trial call 2 succeeds -> Transitions to CLOSED
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_manual_trip_and_reset():
    """Tests manual chaos injection via trip() and restoration via reset()."""
    cb = CircuitBreakerService(name="manual_test")
    assert cb.state == CircuitState.CLOSED

    cb.trip("Chaos drill: simulated cloud partition")
    assert cb.state == CircuitState.OPEN
    telemetry = cb.get_telemetry()
    assert telemetry["fallback_active"] is True
    assert "Chaos drill" in telemetry["last_failure_reason"]

    cb.reset("Drill concluded")
    assert cb.state == CircuitState.CLOSED
    telemetry_after = cb.get_telemetry()
    assert telemetry_after["fallback_active"] is False


def test_circuit_breaker_fail_open_under_simulated_outage():
    """Verifies that ShockTranslator succeeds with fallback even when upstream LLM throws."""
    class CrashingRouter:
        def complete_structured(self, *args, **kwargs):
            # Simulate upstream LLM 503 Service Unavailable
            cb = CircuitBreakerService(name="crash_test", failure_threshold=1)
            cb.trip("503 Service Unavailable")
            mock = kwargs.get("mock_response")
            if mock is not None:
                return mock
            raise RuntimeError("Upstream LLM completely down")

    translator = ShockTranslator(router=CrashingRouter())
    result = translator.translate_prompt("A sudden blockade halts TSMC wafer exports from Taiwan")

    assert isinstance(result, ShockTranslationResponse)
    assert len(result.impulses) > 0
    # Must capture the foundry shock via rule fallback
    foundry_imp = next((imp for imp in result.impulses if imp.node_id == "FOUNDRY_TW"), None)
    assert foundry_imp is not None
    assert foundry_imp.shock_value < 0.0


def test_comprehensive_chaos_suite_all_pass():
    """Executes the master chaos battery and asserts 100% pass across all tests."""
    reports = run_comprehensive_chaos_suite()
    assert len(reports) >= 6

    for r in reports:
        assert r.passed is True, f"Chaos test '{r.test_name}' failed: {r.stability_notes}"
        assert r.nan_or_inf_detected is False, f"NaN or Inf in '{r.test_name}'"
        assert r.execution_time_ms < 5000.0, f"Latency exceeded budget in '{r.test_name}': {r.execution_time_ms}ms"


def test_chaos_api_endpoints():
    """Tests /api/v1/chaos/circuit-breaker, trip, reset, and /api/v1/chaos/drill endpoints."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # 1. Check Circuit Breaker Telemetry
    resp = client.get("/api/v1/chaos/circuit-breaker")
    assert resp.status_code == 200
    data = resp.json()
    assert "llm_router" in data
    assert "ais_feed" in data
    assert data["llm_router"]["state"] in ("CLOSED", "OPEN", "HALF_OPEN")

    # 2. Trip Breaker via API
    trip_resp = client.post(
        "/api/v1/chaos/circuit-breaker/trip",
        json={"name": "llm_router", "reason": "Automated chaos API test"},
    )
    assert trip_resp.status_code == 200
    assert trip_resp.json()["telemetry"]["state"] == "OPEN"

    # 3. Health check reflects tripped circuit breaker
    health_resp = client.get("/api/v1/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["circuit_breakers"]["llm_router"] == "OPEN"
    assert health_resp.json()["circuit_breakers"]["fallback_active"] is True

    # 4. Reset Breaker via API
    reset_resp = client.post(
        "/api/v1/chaos/circuit-breaker/reset",
        json={"name": "llm_router", "reason": "Restoring after API test"},
    )
    assert reset_resp.status_code == 200
    assert reset_resp.json()["telemetry"]["state"] == "CLOSED"

    # 5. Execute Full Chaos Drill Endpoint
    drill_resp = client.post("/api/v1/chaos/drill")
    assert drill_resp.status_code == 200
    drill_data = drill_resp.json()
    assert drill_data["status"] == "PASSED"
    assert drill_data["total_drills"] >= 6
    assert drill_data["passed_count"] == drill_data["total_drills"]

