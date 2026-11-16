"""Threat Intelligence & AIS Maritime Telemetry Service.

Maintains live state, seeds real-world threat feeds, computes SVI,
and provides simulation injection to the API gateway.
"""

from dataclasses import asdict
from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional

from app.engine.ais_threat import (
    AISThreatEngine,
    ChokePointTelemetry,
    ChokePointStatus,
    ThreatEvent,
    ThreatSeverity,
    AISThreatSnapshot,
)


class ThreatIntelligenceService:
    def __init__(self):
        self.engine = AISThreatEngine()
        self.choke_points: Dict[str, ChokePointTelemetry] = {}
        self.active_threats: Dict[str, ThreatEvent] = {}
        self.history: List[Dict[str, Any]] = []
        self._initialize_baseline_state()

    def _initialize_baseline_state(self) -> None:
        """Initializes canonical choke points and active seed threat events."""
        # 1. Initialize Choke Points
        for cp_id, data in self.engine.baseline_choke_points.items():
            telemetry = ChokePointTelemetry(
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
            telemetry.compute_metrics()
            self.choke_points[cp_id] = telemetry

        # 2. Seed Realistic Geopolitical Threat Intelligence Alerts
        seed_threats = [
            ThreatEvent(
                event_id="THR-2026-TW-001",
                timestamp=datetime.now(timezone.utc).isoformat(),
                headline="Taiwan Strait: PLA Naval Live-Fire Exercise Closes Commercial Lanes for 72h",
                source="Reuters Maritime Wire / AIS Satellite Constellation",
                severity=ThreatSeverity.CRITICAL,
                choke_point_id="GEO_TAIWAN_STRAIT",
                affected_nodes=["TSM", "2317_TW", "NVDA", "AAPL", "QCOM", "AMD"],
                raw_supply_impact_pct=-0.38,
                details="Satellite AIS indicates 42 commercial container vessels anchored outside Kaohsiung port. Transit speed collapsed to 3.2 knots across southern exclusion zone.",
                injected=False,
            ),
            ThreatEvent(
                event_id="THR-2026-ML-002",
                timestamp=datetime.now(timezone.utc).isoformat(),
                headline="Strait of Malacca: Supertanker Collision & Oil Slick Forces 12-Hour Traffic Queue",
                source="Singapore Port Authority (MPA) Flash Notice",
                severity=ThreatSeverity.HIGH,
                choke_point_id="GEO_MALACCA",
                affected_nodes=["PORT_RTM", "PORT_LA", "XOM", "CVX", "F"],
                raw_supply_impact_pct=-0.22,
                details="VLCC tanker collision off Phillips Channel restricts eastbound deep-draft passage. Demurrage rates surged 34% intraday.",
                injected=False,
            ),
            ThreatEvent(
                event_id="THR-2026-SZ-003",
                timestamp=datetime.now(timezone.utc).isoformat(),
                headline="Suez Canal / Red Sea: Drone Recon Activity Escalation Triggers Cape Diversions",
                source="UK Maritime Trade Operations (UKMTO)",
                severity=ThreatSeverity.HIGH,
                choke_point_id="GEO_SUEZ",
                affected_nodes=["PORT_RTM", "ASML", "BMW", "F"],
                raw_supply_impact_pct=-0.28,
                details="Major container liner consortia reroute 18 vessels around Cape of Good Hope (+14 days transit delay).",
                injected=False,
            ),
            ThreatEvent(
                event_id="THR-2026-HZ-004",
                timestamp=datetime.now(timezone.utc).isoformat(),
                headline="Strait of Hormuz: War-Risk Surcharges Jump 45% Following Fast-Patrol Interceptions",
                source="Lloyd's Joint War Committee Advisory",
                severity=ThreatSeverity.MEDIUM,
                choke_point_id="GEO_HORMUZ",
                affected_nodes=["XOM", "CVX", "DAL", "UAL"],
                raw_supply_impact_pct=-0.16,
                details="Petroleum tanker insurance underwriters declare enhanced war-risk premium zone across eastern Oman Gulf approach.",
                injected=False,
            ),
            ThreatEvent(
                event_id="THR-2026-PN-005",
                timestamp=datetime.now(timezone.utc).isoformat(),
                headline="Panama Canal: Gatun Lake Draft Restrictions Limit Daily Panamax Transits to 24 Vessels",
                source="Panama Canal Authority (ACP) Advisory",
                severity=ThreatSeverity.LOW,
                choke_point_id="GEO_PANAMA",
                affected_nodes=["PORT_LA", "CAT", "DE"],
                raw_supply_impact_pct=-0.10,
                details="El Niño drought conditions reduce maximum transit draft from 50ft to 44ft, limiting grain and LNG carrier load factors.",
                injected=False,
            ),
        ]

        for t in seed_threats:
            self.active_threats[t.event_id] = t

        # Perform initial telemetry degradation step based on seed threats
        self.advance_telemetry_tick()

    def advance_telemetry_tick(self) -> AISThreatSnapshot:
        """Simulates live vessel drift, queue congestion updates, and SVI index calculation."""
        current_list = list(self.choke_points.values())
        threat_list = list(self.active_threats.values())

        updated_cps, svi = self.engine.simulate_telemetry_step(
            current_telemetries=current_list, active_threats=threat_list
        )

        for cp in updated_cps:
            self.choke_points[cp.choke_point_id] = cp

        total_vessels = sum(cp.current_vessel_count for cp in updated_cps)
        vulnerable_assets = sorted(
            list({node for t in threat_list for node in t.affected_nodes})
        )

        snapshot = AISThreatSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            systemic_vulnerability_index=svi,
            choke_points=updated_cps,
            active_threats=threat_list,
            total_active_vessels=total_vessels,
            vulnerable_assets=vulnerable_assets,
        )
        return snapshot

    def get_snapshot(self) -> Dict[str, Any]:
        """Returns the current state formatted for API responses."""
        cp_list = list(self.choke_points.values())
        svi = self.engine.compute_systemic_vulnerability_index(cp_list)
        threat_list = list(self.active_threats.values())
        total_vessels = sum(cp.current_vessel_count for cp in cp_list)
        vulnerable_assets = sorted(
            list({node for t in threat_list for node in t.affected_nodes})
        )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "systemic_vulnerability_index": svi,
            "total_active_vessels": total_vessels,
            "vulnerable_assets": vulnerable_assets,
            "choke_points": [asdict(cp) for cp in cp_list],
            "active_threats": [asdict(t) for t in threat_list],
        }

    def ingest_threat_event(
        self,
        headline: str,
        source: str,
        severity: str,
        choke_point_id: str,
        affected_nodes: List[str],
        raw_supply_impact_pct: float,
        details: str,
    ) -> ThreatEvent:
        """Allows external webhooks or analysts to post a new breaking threat."""
        event_id = f"THR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        threat = ThreatEvent(
            event_id=event_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            headline=headline,
            source=source,
            severity=ThreatSeverity(severity),
            choke_point_id=choke_point_id,
            affected_nodes=affected_nodes,
            raw_supply_impact_pct=raw_supply_impact_pct,
            details=details,
            injected=False,
        )
        self.active_threats[event_id] = threat
        self.advance_telemetry_tick()
        return threat

    def inject_threat_to_scenario(self, event_id: str) -> Dict[str, Any]:
        """Translates a threat event into a direct impulse vector s^(0) ready for propagation."""
        threat = self.active_threats.get(event_id)
        if not threat:
            raise KeyError(f"Threat event '{event_id}' not found.")

        threat.injected = True
        impulses = self.engine.translate_threat_to_direct_impulses(threat)

        return {
            "event_id": threat.event_id,
            "headline": threat.headline,
            "severity": threat.severity.value,
            "choke_point_id": threat.choke_point_id,
            "direct_impulses": impulses,
            "recommended_scenario_name": f"Live Threat Injection: {threat.headline[:45]}...",
        }


# Global singleton instance
threat_intelligence_service = ThreatIntelligenceService()
