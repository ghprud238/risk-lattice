"""Integration tests for all newly added Institutional Enterprise Services & Endpoints.
PRD Section 16 & Section 24.1 compliant:
- Verifies:
  1. /api/v1/liquidity/simulate
  2. /api/v1/mutation/evaluate
  3. /api/v1/edgar/status & /api/v1/edgar/ingest
  4. /api/v1/pms/aladdin/import & /api/v1/regulatory/ccar/export
  5. /api/v1/copilot/chat
  6. /api/v1/alerts & /api/v1/alerts/test
  7. /api/v1/graph/geospatial
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liquidity_simulation_endpoint():
    payload = {
        "liquidation_pct": 0.20,
        "fund_unencumbered_cash": 15_000_000.0,
        "portfolio_unhedged_pnl": -22_000_000.0,
    }
    resp = client.post("/api/v1/liquidity/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_notional_liquidated"] > 0
    assert data["total_market_impact_loss"] > 0
    assert "margin_summary" in data
    assert data["margin_summary"]["margin_call_cash_drain"] > 0


def test_mutation_evaluation_endpoint():
    payload = {
        "mutation_name": "Arizona Packaging Dual Sourcing",
    }
    resp = client.post("/api/v1/mutation/evaluate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["capital_savings"] > 0
    assert data["resilience_roi_multiple"] > 0
    assert "cvar_relief_pct" in data


def test_edgar_crawler_endpoints():
    # 1. Status
    resp = client.get("/api/v1/edgar/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_active"] is True
    assert len(data["recent_filings"]) > 0

    # 2. Ingest
    ingest_payload = {
        "ticker": "TSLA",
        "filing_type": "10-K",
        "accession_number": "0001318605-26-000018",
        "filing_text": "We depend on our single foundry partner, TSMC, for self-driving FSD chip production.",
    }
    ingest_resp = client.post("/api/v1/edgar/ingest", json=ingest_payload)
    assert ingest_resp.status_code == 200
    ingest_data = ingest_resp.json()
    assert len(ingest_data["discovered_edges"]) >= 1


def test_institutional_adapters_and_ccar_endpoint():
    # 1. Aladdin CSV Import
    aladdin_csv = """TICKER,ASSET_CLASS,NOTIONAL
NVDA,EQUITY,25000000
TSM,EQUITY,20000000
AAPL,EQUITY,20000000
F,EQUITY,10000000
"""
    imp_resp = client.post("/api/v1/pms/aladdin/import", json={"csv_content": aladdin_csv})
    assert imp_resp.status_code == 200
    imp_data = imp_resp.json()
    assert imp_data["total_positions"] == 4

    # 2. CCAR FR Y-14A Export
    ccar_payload = {
        "portfolio_notional": 100_000_000.0,
        "pnl_loss": -23_450_000.0,
        "cvar_99": 29_312_500.0,
        "var_95": 21_200_000.0,
    }
    ccar_resp = client.post("/api/v1/regulatory/ccar/export", json=ccar_payload)
    assert ccar_resp.status_code == 200
    ccar_data = ccar_resp.json()
    assert ccar_data["regulatory_form"] == "FR Y-14A"
    assert len(ccar_data["schedule_items"]) >= 4


def test_copilot_chat_endpoint():
    chat_payload = {
        "query": "What is our exposure to TSMC Fab 18 in Taiwan?",
        "portfolio_notional": 100_000_000.0,
    }
    resp = client.post("/api/v1/copilot/chat", json=chat_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "SEMICONDUCTOR_EXPOSURE_QUERY"
    assert "TSMC" in data["headline"]
    assert len(data["recommended_actions"]) > 0


def test_alerting_and_geospatial_endpoints():
    # 1. Alert test
    alert_payload = {
        "scenario_name": "Red Sea Missile Escalation",
        "portfolio_notional": 100_000_000.0,
        "pnl_loss": -22_000_000.0,
        "cvar_99": 27_500_000.0,
        "limit_drawdown_pct": -15.0,
    }
    alt_resp = client.post("/api/v1/alerts/test", json=alert_payload)
    assert alt_resp.status_code == 200
    alt_data = alt_resp.json()
    assert alt_data["alert"]["severity"] in ("WARNING", "CRITICAL")
    assert "slack_payload" in alt_data

    # 2. List alerts
    list_resp = client.get("/api/v1/alerts")
    assert list_resp.status_code == 200
    assert len(list_resp.json()["alerts"]) >= 1

    # 3. Geospatial coordinates
    geo_resp = client.get("/api/v1/graph/geospatial")
    assert geo_resp.status_code == 200
    geo_data = geo_resp.json()
    assert len(geo_data["facilities"]) >= 5
    assert len(geo_data["corridors"]) >= 3
