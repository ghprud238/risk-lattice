"""Typed domain models and validation per Section 15 and 12.1.
Strictly frozen, extra=forbid, with finite floats and canonical structures.
"""

from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field
from pydantic.types import FiniteFloat


class JobState(str, Enum):
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    RUNNING = "RUNNING"
    VALIDATING = "VALIDATING"
    COMMITTING = "COMMITTING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ShockPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    t: FiniteFloat
    value: FiniteFloat


class FactorShock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    factor_id: str = Field(min_length=1, max_length=100)
    unit: Literal["bps", "fraction", "price_fraction", "index_points"]
    kind: Literal["instant_delta", "level_path", "increment_path"]
    baseline_id: str = Field(default="DEFAULT")
    horizon_days: int = Field(default=20, ge=1, le=252)
    points: Tuple[ShockPoint, ...] = Field(min_length=1, max_length=1000)


class ScenarioDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1"] = "1"
    shocks: Tuple[FactorShock, ...] = ()
    unresolved: Tuple[str, ...] = ()
    assumptions: Tuple[str, ...] = ()


class ApprovedScenario(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    scenario_id: str
    schema_version: Literal["1"] = "1"
    shocks: Tuple[FactorShock, ...]
    assumptions: Tuple[str, ...] = ()
    content_hash: str
    approved_at: str

    @classmethod
    def create(cls, scenario_id: str, shocks: Tuple[FactorShock, ...], assumptions: Tuple[str, ...], approved_at: str) -> "ApprovedScenario":
        # Deterministic SHA256 of shocks content
        payload = {
            "shocks": [
                {
                    "factor_id": s.factor_id,
                    "unit": s.unit,
                    "kind": s.kind,
                    "baseline_id": s.baseline_id,
                    "horizon_days": s.horizon_days,
                    "points": [{"t": p.t, "value": p.value} for p in s.points]
                }
                for s in shocks
            ],
            "assumptions": list(assumptions),
        }
        raw_json = json.dumps(payload, sort_keys=True)
        content_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
        return cls(
            scenario_id=scenario_id,
            schema_version="1",
            shocks=shocks,
            assumptions=assumptions,
            content_hash=content_hash,
            approved_at=approved_at,
        )


class HoldingItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    node_id: str
    ticker: str
    notional: FiniteFloat
    weight: FiniteFloat
    asset_class: str
    currency: str = "USD"


class PortfolioVersion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    portfolio_version_id: str
    portfolio_id: str
    base_currency: str = "USD"
    as_of: str
    holdings: Tuple[HoldingItem, ...]
    content_hash: str


class SimulateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1"] = "1"
    portfolio_version_id: str
    graph_version_id: str
    scenario_version_id: str
    engine_profile: str = "four-hop-v2"
    risk_profile: str = "residual-tcopula-v1"
    seed: int = 42
    paths: int = 10000


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1"] = "1"
    run_id: str
    portfolio_version_id: str
    graph_version_id: str
    scenario_version_id: str
    engine_profile: str
    risk_profile: str
    seed: int
    paths: int
    created_at: str
    status: JobState = JobState.QUEUED
    attempt_id: str = "attempt-0"
    completed_at: Optional[str] = None
    content_hash: Optional[str] = None
