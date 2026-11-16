"""Unit & Integration Tests for AIS Maritime Telemetry & Threat Intelligence Engine."""

import pytest
from fastapi.testclient import TestClient

from app.engine.ais_threat import (
    AISThreatEngine,
    ChokePointTelemetry,
    ChokePointStatus,
    ThreatEvent,
    ThreatSeverity,
)
from app.services.threat_intelligence_service import ThreatIntelligenceService
from app.main import app


@pytest.fixture
def engine():
    return AISThreatEngine()


@pytest.fixture
def service():
    return ThreatIntelligenceService()


@pytest.fixture
def client():
    return TestClient(app)


def test_choke_point_telemetry_metrics(engine):
    """Verifies non-linear congestion index and demurrage surge calculations."""
    telemetry = ChokePointTelemetry(
        choke_point_id="GEO_TAIWAN_STRAIT",
        name="Taiwan Strait Corridor",
        lat=24.5,
        lng=119.8,
        baseline_daily_vessels=200,
        current_vessel_count=400,  # 2.0x volume queue
        transit_speed_knots=4.0,   # Speed collapsed from 16.0 to 4.0
        baseline_speed_knots=16.0,
        status=ChokePointStatus.MILITARY_EXERCISE,
        criticality_weight=0.35,
    )
    telemetry.compute_metrics()

    # Congestion index should be significantly elevated (> 4.0)
    assert telemetry.congestion_index > 4.0
    assert telemetry.demurrage_spike_pct > 100.0  # charter rates more than double
    assert telemetry.disruption_probability > 0.80  # high disruption probability


def test_systemic_vulnerability_index_bounds(engine):
    """Verifies that the SVI index stays bounded in [0, 100] and increases monotonically with stress."""
    # 1. Normal conditions
    normal_cps = [
        ChokePointTelemetry(
            choke_point_id=cp_id,
            name=data["name"],
            lat=data["lat"],
            lng=data["lng"],
            baseline_daily_vessels=data["baseline_daily_vessels"],
            current_vessel_count=data["baseline_daily_vessels"],
            transit_speed_knots=data["baseline_speed_knots"],
            baseline_speed_knots=data["baseline_speed_knots"],
            status=ChokePointStatus.NORMAL,
            criticality_weight=data["criticality_weight"],
        )
        for cp_id, data in engine.baseline_choke_points.items()
    ]
    svi_normal = engine.compute_systemic_vulnerability_index(normal_cps)
    assert 0.0 <= svi_normal <= 15.0

    # 2. Severe Blockade conditions on Taiwan Strait
    stressed_cps = [
        ChokePointTelemetry(
            choke_point_id="GEO_TAIWAN_STRAIT",
            name="Taiwan Strait",
            lat=24.5,
            lng=119.8,
            baseline_daily_vessels=240,
            current_vessel_count=600,
            transit_speed_knots=2.0,
            baseline_speed_knots=16.5,
            status=ChokePointStatus.BLOCKADE,
            criticality_weight=0.35,
        )
    ]
    svi_stressed = engine.compute_systemic_vulnerability_index(stressed_cps)
    assert svi_stressed > svi_normal


def test_translate_threat_to_direct_impulses(engine):
    """Verifies that threat events translate into decaying initial shock vectors."""
    threat = ThreatEvent(
        event_id="TEST-001",
        timestamp="2026-11-16T10:00:00Z",
        headline="Taiwan Strait Crisis",
        source="Test Wire",
        severity=ThreatSeverity.CRITICAL,
        choke_point_id="GEO_TAIWAN_STRAIT",
        affected_nodes=["TSM", "NVDA", "AAPL"],
        raw_supply_impact_pct=-0.40,
        details="Naval blockade in effect.",
    )
    impulses = engine.translate_threat_to_direct_impulses(threat)

    assert "TSM" in impulses
    assert "NVDA" in impulses
    assert "AAPL" in impulses
    # Primary node takes largest shock; subsequent nodes decay
    assert impulses["TSM"] <= impulses["NVDA"]
    assert impulses["NVDA"] <= impulses["AAPL"]
    assert -0.95 <= impulses["TSM"] < 0.0


def test_threat_intelligence_service_lifecycle(service):
    """Verifies service advancement, custom threat ingestion, and scenario injection."""
    initial_snapshot = service.get_snapshot()
    assert initial_snapshot["total_active_vessels"] > 0
    assert len(initial_snapshot["choke_points"]) == 5
    assert len(initial_snapshot["active_threats"]) >= 5

    # Advance telemetry
    new_snapshot = service.advance_telemetry_tick()
    assert new_snapshot.systemic_vulnerability_index >= 0.0

    # Inject threat into scenario
    first_threat = initial_snapshot["active_threats"][0]
    injection = service.inject_threat_to_scenario(first_threat["event_id"])
    assert "direct_impulses" in injection
    assert len(injection["direct_impulses"]) > 0
    assert "Live Threat Injection" in injection["recommended_scenario_name"]


def test_threat_api_endpoints(client):
    """Verifies all FastAPI threat intelligence endpoints."""
    # 1. GET status
    res = client.get("/api/v1/threats/ais/status")
    assert res.status_code == 200
    data = res.json()
    assert "systemic_vulnerability_index" in data
    assert len(data["choke_points"]) == 5

    # 2. POST tick
    res_tick = client.post("/api/v1/threats/ais/tick")
    assert res_tick.status_code == 200
    assert "total_active_vessels" in res_tick.json()

    # 3. POST ingest custom threat
    payload = {
        "headline": "Malacca Strait Fuel Tanker Grounding Shuts Inbound Lanes",
        "source": "Singapore Maritime Command",
        "severity": "HIGH",
        "choke_point_id": "GEO_MALACCA",
        "affected_nodes": ["PORT_RTM", "XOM", "CVX"],
        "raw_supply_impact_pct": -0.25,
        "details": "Vessel grounded off Raffles Lighthouse.",
    }
    res_ingest = client.post("/api/v1/threats/ingest", json=payload)
    assert res_ingest.status_code == 200
    new_event_id = res_ingest.json()["event_id"]

    # 4. POST inject threat into simulation
    res_inject = client.post("/api/v1/threats/inject", json={"event_id": new_event_id})
    assert res_inject.status_code == 200
    inj_data = res_inject.json()
    assert "direct_impulses" in inj_data
    assert "PORT_RTM" in inj_data["direct_impulses"]
