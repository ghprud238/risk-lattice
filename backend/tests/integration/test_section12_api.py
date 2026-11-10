"""Integration Tests for Expanded PRD Section 12 REST API Contracts.
Tests scenario draft/approval workflow, portfolio versioning, run state tracking, and error envelopes.
"""

from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


def test_scenario_draft_and_approval_workflow():
    # 1. Create a draft scenario
    draft_payload = {
        "shocks": [
            {
                "factor_id": "US10Y_REAL",
                "unit": "bps",
                "kind": "instant_delta",
                "points": [{"t": 0.0, "value": 150.0}],
            },
            {
                "factor_id": "BRENT_CRUDE",
                "unit": "price_fraction",
                "kind": "instant_delta",
                "points": [{"t": 0.0, "value": 0.35}],
            },
        ],
        "assumptions": ["Stagflationary rate and energy shock"],
    }
    draft_res = client.post("/api/v1/scenarios/draft", json=draft_payload)
    assert draft_res.status_code == 200
    draft_data = draft_res.json()
    assert "draft_id" in draft_data
    draft_id = draft_data["draft_id"]

    # 2. Approve scenario into immutable version
    approve_res = client.post(f"/api/v1/scenarios/{draft_id}/approve")
    assert approve_res.status_code == 200
    approved_data = approve_res.json()
    assert approved_data["scenario_id"] == draft_id
    assert "content_hash" in approved_data
    assert len(approved_data["content_hash"]) == 64


def test_scenario_draft_unit_mismatch_rejection():
    # Attempt to draft with wrong unit for factor (bps instead of price_fraction for BRENT_CRUDE)
    bad_payload = {
        "shocks": [
            {
                "factor_id": "BRENT_CRUDE",
                "unit": "bps",  # Invalid! Canonical unit is price_fraction
                "kind": "instant_delta",
                "points": [{"t": 0.0, "value": 500.0}],
            }
        ]
    }
    draft_res = client.post("/api/v1/scenarios/draft", json=bad_payload)
    assert draft_res.status_code == 200
    draft_id = draft_res.json()["draft_id"]

    # Approval should be rejected with 422 and INPUT_UNIT_MISMATCH
    approve_res = client.post(f"/api/v1/scenarios/{draft_id}/approve")
    assert approve_res.status_code == 422
    err_data = approve_res.json()
    assert "error" in err_data
    assert err_data["error"]["code"] == "INPUT_UNIT_MISMATCH"


def test_portfolio_version_approval():
    holdings = [
        {"ticker": "NVDA", "notional": 500000.0},
        {"ticker": "TSM", "notional": 500000.0},
    ]
    res = client.post(
        "/api/v1/portfolios/PORT_CORE/versions",
        json={"holdings": holdings},
    )
    assert res.status_code == 200
    data = res.json()
    assert "portfolio_version_id" in data
    assert "content_hash" in data
    assert len(data["holdings"]) == 2


def test_run_lifecycle_and_cancellation():
    from app.services import job_service
    run_id, _ = job_service.create_job(
        portfolio_version_id="pv-001",
        graph_version_id="gv-001",
        scenario_version_id="sv-001",
    )

    # Inspect run status
    res = client.get(f"/api/v1/runs/{run_id}")
    assert res.status_code == 200
    assert res.json()["run_id"] == run_id
    assert res.json()["status"] == "QUEUED"

    # Cancel run
    cancel_res = client.delete(f"/api/v1/runs/{run_id}")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["cancelled"] is True

    # Re-check status is CANCELLED
    res_after = client.get(f"/api/v1/runs/{run_id}")
    assert res_after.json()["status"] == "CANCELLED"
