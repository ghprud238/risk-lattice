"""
Integration Tests for ContagionGraph FastAPI Gateway.
PRD Milestone 4:
- Verifies all REST endpoints and data contracts
- Enforces response schemas and performance latency
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["total_nodes"] == 50
    assert data["total_edges"] >= 50


def test_graph_endpoint():
    response = client.get("/api/v1/graph")
    assert response.status_code == 200
    data = response.json()
    elements = data["elements"]
    assert len(elements["nodes"]) == 50
    assert len(elements["edges"]) >= 50

    # Verify node data attributes
    sample_node = elements["nodes"][0]["data"]
    assert "id" in sample_node
    assert "type" in sample_node
    assert "substitutability" in sample_node


def test_portfolio_ingest_sanitization():
    payload = {
        "name": "Quant Tech Portfolio",
        "holdings": {
            "NVDA": 400000.0,
            "TSLA": 300000.0,
            "BA": 200000.0,
            "F": 100000.0,
            "UNKNOWN_CO": 50000.0
        }
    }
    response = client.post("/api/v1/portfolio/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()

    weights = data["normalized_weights"]
    assert abs(sum(weights.values()) - 1.0) < 1e-3
    assert "UNKNOWN_CO" in data["unrecognized_tickers"]
    assert "NVDA" in weights
    assert weights["NVDA"] == 0.4


def test_stress_simulate_endpoint():
    payload = {
        "scenario_name": "Synthetic Taiwan Foundry Halt",
        "direct_impulses": {
            "FOUNDRY_TW": -0.70,
            "BALTIC_DRY": 1.80
        },
        "portfolio_weights": {
            "TSLA": 0.33,
            "F": 0.33,
            "GM": 0.34
        }
    }
    response = client.post("/api/v1/stress/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "simulation" in data
    assert "risk_metrics" in data
    assert "narrative" in data

    sim = data["simulation"]
    assert len(sim["node_shocks"]) == 50
    assert "TSLA" in sim["node_shocks"]
    assert sim["node_shocks"]["TSLA"]["cumulative_shock"] < 0

    pnl = sim["portfolio_pnl"]
    assert pnl["total_pnl"] < 0
    # Audit log check: hop1 + hop2 + hop3_4 == total_pnl
    assert abs(pnl["hop1_pnl"] + pnl["hop2_pnl"] + pnl["hop3_4_pnl"] - pnl["total_pnl"]) < 1e-4

    narrative = data["narrative"]
    assert narrative["citations_verified"] is True


def test_backtest_run_endpoint():
    response = client.post("/api/v1/backtest/run", json={"scenario_id": "all"})
    assert response.status_code == 200
    data = response.json()

    assert "scenarios" in data
    assert len(data["scenarios"]) == 4
    for sc in data["scenarios"]:
        assert sc["metric_achieved"] is True

    assert "kupiec_pof" in data
    assert data["kupiec_pof"]["passed"] is True

    assert "discovery_lift" in data
    assert data["discovery_lift"]["f1_score"] >= 0.80
