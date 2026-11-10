"""Domain layer containing frozen contracts, error codes, and factor registry.
"""

from app.domain.errors import FailureCode, ErrorDetail, ErrorEnvelope, ContagionDomainException
from app.domain.models import (
    JobState,
    ShockPoint,
    FactorShock,
    ScenarioDraft,
    ApprovedScenario,
    HoldingItem,
    PortfolioVersion,
    SimulateRequest,
    RunManifest,
)
from app.domain.factor_registry import FACTOR_REGISTRY, FactorDefinition, validate_factor_shock

__all__ = [
    "FailureCode",
    "ErrorDetail",
    "ErrorEnvelope",
    "ContagionDomainException",
    "JobState",
    "ShockPoint",
    "FactorShock",
    "ScenarioDraft",
    "ApprovedScenario",
    "HoldingItem",
    "PortfolioVersion",
    "SimulateRequest",
    "RunManifest",
    "FACTOR_REGISTRY",
    "FactorDefinition",
    "validate_factor_shock",
]
