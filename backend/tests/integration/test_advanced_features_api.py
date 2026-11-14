"""Integration tests for all newly added Advanced Risk & Governance API endpoints.
PRD Section 16 & Section 24.1 compliant:
- Verifies HTTP request/response schemas, JSON serialization, and error handling for:
  1. /api/v1/optimize/hedge
  2. /api/v1/stress/reverse
  3. /api/v1/stress/timeline
  4. /api/v1/scenario/diff
  5. /api/v1/audit/* (Submit, Approve, Lock, Entries)
  6. /api/v1/report/executive
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_hedge_optimizer_api():
    payload = {
        "portfolio_notional": 100_000_000.0,
        "unhedged_pnl": -22_500_000.0,
        "node_shocks": {"TSM": -0.35, "NVDA": -0.30},
        "budget_limit": 500_000.0,
    }
    resp = client.post("/api/v1/optimize/hedge", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["pnl_improvement"] > 0.0
    assert data["total_hedge_cost"] <= 500_000.0
    assert len(data["recommendations"]) > 0
    assert len(data["efficient_frontier"]) == 5


def test_reverse_stress_api():
    payload = {
        "portfolio_notional": 100_000_000.0,
        "target_loss_pct": 0.20,
    }
    resp = client.post("/api/v1/stress/reverse", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["achieved_loss_pct"] >= 0.199
    assert data["norm_l2"] > 0
    assert len(data["minimal_shocks"]) > 0


def test_timeline_simulation_api():
    payload = {
        "initial_shocks": {"TSM": -0.40},
        "portfolio_notional": 100_000_000.0,
        "time_horizon_days": [0, 7, 14, 30, 45, 60, 90],
    }
    resp = client.post("/api/v1/stress/timeline", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["steps"]) == 7
    assert data["peak_drawdown_pnl"] < 0
    assert data["total_milestones"] > 0


def test_scenario_diff_api():
    payload = {
        "scenario_a_name": "Base Shock",
        "scenario_b_name": "Resilient Graph",
        "shocks_a": {"TSM": -0.40, "NVDA": -0.35},
        "shocks_b": {"TSM": -0.15, "NVDA": -0.10},
        "positions": {"TSM": 20_000_000.0, "NVDA": 25_000_000.0},
    }
    resp = client.post("/api/v1/scenario/diff", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["delta_pnl"] > 0
    assert data["de_risked_nodes_count"] >= 2


def test_audit_governance_and_executive_report_api():
    # 1. Submit for review
    submit_payload = {
        "run_id": "api-run-citadel-777",
        "scenario_name": "Semiconductor Fab Fire",
        "submitted_by": "analyst.elena@citadel.com",
        "submitted_by_role": "ANALYST",
        "pnl_impact": -18_200_000.0,
        "cvar_99": 22_750_000.0,
        "shock_summary": {"TSM": -0.45},
    }
    sub_resp = client.post("/api/v1/audit/submit", json=submit_payload)
    assert sub_resp.status_code == 200
    assert sub_resp.json()["entry"]["status"] == "PENDING_REVIEW"

    # 2. Four-Eyes validation: Submitter cannot approve
    bad_approve_payload = {
        "run_id": "api-run-citadel-777",
        "approver_email": "analyst.elena@citadel.com",
        "approver_role": "CHIEF_RISK_OFFICER",
    }
    bad_resp = client.post("/api/v1/audit/approve", json=bad_approve_payload)
    assert bad_resp.status_code == 400

    # 3. CRO approves
    good_approve_payload = {
        "run_id": "api-run-citadel-777",
        "approver_email": "cro.sarah@citadel.com",
        "approver_role": "CHIEF_RISK_OFFICER",
        "comments": "Approved with $500k put hedge buffer.",
    }
    good_resp = client.post("/api/v1/audit/approve", json=good_approve_payload)
    assert good_resp.status_code == 200
    assert good_resp.json()["entry"]["status"] == "APPROVED_BY_CRO"
    assert len(good_resp.json()["entry"]["cryptographic_seal_sha256"]) == 64

    # 4. Auditor locks regulatory packet
    lock_payload = {
        "run_id": "api-run-citadel-777",
        "auditor_email": "auditor.internal@citadel.com",
    }
    lock_resp = client.post("/api/v1/audit/lock", json=lock_payload)
    assert lock_resp.status_code == 200
    assert lock_resp.json()["governance_status"] == "COMPLIANT_SR_11_7"

    # 5. List entries
    list_resp = client.get("/api/v1/audit/entries")
    assert list_resp.status_code == 200
    assert len(list_resp.json()["entries"]) >= 2

    # 6. Executive Report generation
    memo_payload = {
        "scenario_name": "Taiwan Foundry Disruption",
        "portfolio_notional": 100_000_000.0,
        "pnl_loss": -23_450_000.0,
        "cvar_99": 29_312_500.0,
        "var_95": 21_200_000.0,
    }
    memo_resp = client.post("/api/v1/report/executive", json=memo_payload)
    assert memo_resp.status_code == 200
    memo_data = memo_resp.json()
    assert "html_content" in memo_data
    assert "<!DOCTYPE html>" in memo_data["html_content"]
