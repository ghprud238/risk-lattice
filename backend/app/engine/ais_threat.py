"""AIS Maritime Telemetry & Geopolitical Threat Intelligence Engine.

Pure deterministic scientific engine (ADR-002 compliant).
Zero imports from databases, web frameworks, or LLM clients.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Dict, List, Optional, Tuple
import numpy as np


class ChokePointStatus(str, Enum):
    NORMAL = "NORMAL"
    ELEVATED_QUEUE = "ELEVATED_QUEUE"
    WEATHER_ALERT = "WEATHER_ALERT"
    MILITARY_EXERCISE = "MILITARY_EXERCISE"
    BLOCKADE = "BLOCKADE"
    CANAL_OBSTRUCTION = "CANAL_OBSTRUCTION"


class ThreatSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ChokePointTelemetry:
    choke_point_id: str
    name: str
    lat: float
    lng: float
    baseline_daily_vessels: int
    current_vessel_count: int
    transit_speed_knots: float
    baseline_speed_knots: float
    status: ChokePointStatus
    criticality_weight: float  # Importance to global trade (sum of weights ~ 1.0)
    demurrage_spike_pct: float = 0.0
    congestion_index: float = 1.0
    disruption_probability: float = 0.0

    def compute_metrics(self) -> None:
        """Computes non-linear congestion index and disruption probability."""
        # Speed ratio penalty (if speed drops from 16 to 4 knots, ratio = 4.0)
        speed_safe = max(0.5, self.transit_speed_knots)
        speed_drag = max(1.0, self.baseline_speed_knots / speed_safe)

        # Volume queue ratio
        queue_ratio = max(0.1, self.current_vessel_count / max(1, self.baseline_daily_vessels))

        # Congestion index: multiplicative interaction of queue buildup and speed collapse
        self.congestion_index = round(float(queue_ratio * (speed_drag ** 0.8)), 2)

        # Demurrage cost surge modeled as exponential function of congestion
        self.demurrage_spike_pct = round(float(max(0.0, (self.congestion_index - 1.0) * 45.0)), 1)

        # Disruption probability (logistic activation)
        severity_bonus = 0.0
        if self.status in [ChokePointStatus.MILITARY_EXERCISE, ChokePointStatus.CANAL_OBSTRUCTION]:
            severity_bonus = 0.40
        elif self.status == ChokePointStatus.BLOCKADE:
            severity_bonus = 0.85
        elif self.status == ChokePointStatus.ELEVATED_QUEUE:
            severity_bonus = 0.15

        logit = 2.0 * (self.congestion_index - 1.8) + severity_bonus * 3.0
        self.disruption_probability = round(float(1.0 / (1.0 + math.exp(-logit))), 3)


@dataclass
class ThreatEvent:
    event_id: str
    timestamp: str
    headline: str
    source: str
    severity: ThreatSeverity
    choke_point_id: str
    affected_nodes: List[str]
    raw_supply_impact_pct: float  # e.g. -0.35 for 35% supply degradation
    details: str
    injected: bool = False


@dataclass
class AISThreatSnapshot:
    timestamp: str
    systemic_vulnerability_index: float  # 0 to 100
    choke_points: List[ChokePointTelemetry]
    active_threats: List[ThreatEvent]
    total_active_vessels: int
    vulnerable_assets: List[str]


class AISThreatEngine:
    """Deterministic scientific calculation engine for maritime choke points and geopolitical threats."""

    def __init__(self):
        # Canonical baseline choke points
        self.baseline_choke_points: Dict[str, Dict] = {
            "GEO_TAIWAN_STRAIT": {
                "name": "Taiwan Strait Maritime Corridor",
                "lat": 24.5,
                "lng": 119.8,
                "baseline_daily_vessels": 240,
                "baseline_speed_knots": 16.5,
                "criticality_weight": 0.35,  # 35% weight: 65% of advanced silicon
                "default_affected": ["TSM", "2317_TW", "NVDA", "AAPL", "QCOM", "AMD"],
            },
            "GEO_MALACCA": {
                "name": "Strait of Malacca Gateway",
                "lat": 2.5,
                "lng": 101.5,
                "baseline_daily_vessels": 320,
                "baseline_speed_knots": 15.0,
                "criticality_weight": 0.25,  # 25% weight: crude oil and East Asia electronics
                "default_affected": ["PORT_RTM", "PORT_LA", "XOM", "CVX", "F"],
            },
            "GEO_SUEZ": {
                "name": "Suez Canal / Bab-el-Mandeb",
                "lat": 29.9,
                "lng": 32.5,
                "baseline_daily_vessels": 85,
                "baseline_speed_knots": 12.0,
                "criticality_weight": 0.20,  # 20% weight: Asia-Europe container trade
                "default_affected": ["PORT_RTM", "ASML", "BMW", "F"],
            },
            "GEO_HORMUZ": {
                "name": "Strait of Hormuz Petroleum Corridor",
                "lat": 26.5,
                "lng": 56.2,
                "baseline_daily_vessels": 110,
                "baseline_speed_knots": 14.0,
                "criticality_weight": 0.15,  # 15% weight: 21% of global petroleum liquids
                "default_affected": ["XOM", "CVX", "DAL", "UAL"],
            },
            "GEO_PANAMA": {
                "name": "Panama Canal Continental Lock",
                "lat": 9.1,
                "lng": -79.7,
                "baseline_daily_vessels": 36,
                "baseline_speed_knots": 8.0,
                "criticality_weight": 0.05,  # 5% weight: US Gulf LNG & bulk grain
                "default_affected": ["PORT_LA", "CAT", "DE"],
            },
        }

    def compute_systemic_vulnerability_index(
        self, choke_points: List[ChokePointTelemetry]
    ) -> float:
        """Computes the aggregate Systemic Vulnerability Index (SVI) on a 0 - 100 scale.
        SVI integrates normalized congestion index, speed collapse, and active threat status.
        """
        svi_accum = 0.0
        for cp in choke_points:
            cp.compute_metrics()
            # Normalized stress contribution for this choke point (0.0 to 1.0)
            congestion_contribution = min(1.0, max(0.0, (cp.congestion_index - 1.0) / 2.5))
            status_penalty = 0.0
            if cp.status == ChokePointStatus.BLOCKADE:
                status_penalty = 0.85
            elif cp.status in [ChokePointStatus.MILITARY_EXERCISE, ChokePointStatus.CANAL_OBSTRUCTION]:
                status_penalty = 0.50
            elif cp.status in [ChokePointStatus.ELEVATED_QUEUE, ChokePointStatus.WEATHER_ALERT]:
                status_penalty = 0.20

            choke_stress = min(1.0, 0.6 * congestion_contribution + 0.4 * status_penalty)
            svi_accum += cp.criticality_weight * choke_stress

        svi_score = round(float(svi_accum * 100.0), 1)
        return min(100.0, max(0.0, svi_score))

    def translate_threat_to_direct_impulses(
        self, threat: ThreatEvent
    ) -> Dict[str, float]:
        """Translates a real-time threat intelligence event into an exact initial shock vector s^(0).
        Applies non-linear attenuation based on severity level.
        """
        severity_mult = {
            ThreatSeverity.LOW: 0.40,
            ThreatSeverity.MEDIUM: 0.70,
            ThreatSeverity.HIGH: 1.00,
            ThreatSeverity.CRITICAL: 1.35,
        }.get(threat.severity, 1.0)

        base_shock = -abs(threat.raw_supply_impact_pct) * severity_mult
        base_shock = max(-0.95, min(-0.02, base_shock))

        impulses: Dict[str, float] = {}
        for idx, node in enumerate(threat.affected_nodes):
            # Primary node takes full shock; subsidiary nodes take decaying share
            tier_decay = 1.0 if idx == 0 else max(0.40, 0.85 ** idx)
            impulses[node] = round(float(base_shock * tier_decay), 4)

        return impulses

    def simulate_telemetry_step(
        self,
        current_telemetries: List[ChokePointTelemetry],
        active_threats: List[ThreatEvent],
        noise_factor: float = 0.05,
    ) -> Tuple[List[ChokePointTelemetry], float]:
        """Advances the maritime simulation by one discrete telemetry tick.
        Simulates realistic vessel position drift, queue fluctuations, and speeds.
        """
        updated: List[ChokePointTelemetry] = []
        threat_chokepoints = {t.choke_point_id: t for t in active_threats}

        for cp in current_telemetries:
            base_info = self.baseline_choke_points.get(cp.choke_point_id, {})
            baseline_speed = base_info.get("baseline_speed_knots", 15.0)
            baseline_vessels = base_info.get("baseline_daily_vessels", 100)

            target_status = cp.status
            speed_target = baseline_speed
            vessel_target = baseline_vessels

            # If there's an active threat on this choke point, degrade telemetry
            if cp.choke_point_id in threat_chokepoints:
                th = threat_chokepoints[cp.choke_point_id]
                if th.severity == ThreatSeverity.CRITICAL:
                    target_status = ChokePointStatus.BLOCKADE
                    speed_target = baseline_speed * 0.20  # Ships stopped/rerouting
                    vessel_target = int(baseline_vessels * 2.4)  # Massive queue backlog
                elif th.severity == ThreatSeverity.HIGH:
                    target_status = ChokePointStatus.MILITARY_EXERCISE
                    speed_target = baseline_speed * 0.50
                    vessel_target = int(baseline_vessels * 1.8)
                elif th.severity == ThreatSeverity.MEDIUM:
                    target_status = ChokePointStatus.ELEVATED_QUEUE
                    speed_target = baseline_speed * 0.80
                    vessel_target = int(baseline_vessels * 1.35)

            # Smooth drift towards target with slight Gaussian jitter
            new_speed = max(1.0, cp.transit_speed_knots + 0.3 * (speed_target - cp.transit_speed_knots))
            new_count = max(5, int(cp.current_vessel_count + 0.3 * (vessel_target - cp.current_vessel_count)))

            new_cp = ChokePointTelemetry(
                choke_point_id=cp.choke_point_id,
                name=cp.name,
                lat=cp.lat,
                lng=cp.lng,
                baseline_daily_vessels=cp.baseline_daily_vessels,
                current_vessel_count=new_count,
                transit_speed_knots=round(new_speed, 1),
                baseline_speed_knots=cp.baseline_speed_knots,
                status=target_status,
                criticality_weight=cp.criticality_weight,
            )
            new_cp.compute_metrics()
            updated.append(new_cp)

        svi = self.compute_systemic_vulnerability_index(updated)
        return updated, svi
