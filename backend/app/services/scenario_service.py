"""Scenario Management and Approval Service per Section 15 & 16.
Validates units against canonical FACTOR_REGISTRY and generates immutable SHA256 content hashes.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import uuid

from app.domain.errors import ContagionDomainException, FailureCode
from app.domain.factor_registry import FACTOR_REGISTRY, validate_factor_shock
from app.domain.models import ApprovedScenario, FactorShock, ScenarioDraft, ShockPoint


class ScenarioService:
    def __init__(self):
        self._drafts: Dict[str, ScenarioDraft] = {}
        self._approved: Dict[str, ApprovedScenario] = {}

    def draft_scenario(
        self,
        shocks: List[Dict],
        assumptions: Optional[List[str]] = None,
        unresolved: Optional[List[str]] = None,
    ) -> Tuple[str, ScenarioDraft]:
        draft_id = str(uuid.uuid4())
        parsed_shocks: List[FactorShock] = []

        for s in shocks:
            factor_id = s.get("factor_id", "")
            unit = s.get("unit", "")
            kind = s.get("kind", "instant_delta")
            points_data = s.get("points", [])
            points = tuple(
                ShockPoint(t=float(p.get("t", 0.0)), value=float(p.get("value", 0.0)))
                for p in points_data
            )
            parsed_shocks.append(
                FactorShock(
                    factor_id=factor_id,
                    unit=unit,
                    kind=kind,
                    baseline_id=s.get("baseline_id", "DEFAULT"),
                    horizon_days=int(s.get("horizon_days", 20)),
                    points=points,
                )
            )

        draft = ScenarioDraft(
            schema_version="1",
            shocks=tuple(parsed_shocks),
            unresolved=tuple(unresolved or []),
            assumptions=tuple(assumptions or []),
        )
        self._drafts[draft_id] = draft
        return draft_id, draft

    def approve_scenario(
        self,
        scenario_id: str,
        shocks: Optional[List[FactorShock]] = None,
        assumptions: Optional[List[str]] = None,
    ) -> ApprovedScenario:
        """Approves a scenario draft into an immutable ApprovedScenario.
        Validates canonical units against FACTOR_REGISTRY and asserts zero unresolved fields.
        """
        if scenario_id in self._approved:
            return self._approved[scenario_id]

        if scenario_id in self._drafts:
            draft = self._drafts[scenario_id]
            if draft.unresolved:
                raise ContagionDomainException(
                    code=FailureCode.INPUT_UNIT_MISMATCH,
                    message=f"Cannot approve scenario with unresolved items: {list(draft.unresolved)}",
                    fields=list(draft.unresolved),
                )
            target_shocks = draft.shocks
            target_assumptions = draft.assumptions
        elif shocks is not None:
            target_shocks = tuple(shocks)
            target_assumptions = tuple(assumptions or [])
        else:
            raise ContagionDomainException(
                code=FailureCode.ENTITY_AMBIGUOUS,
                message=f"Scenario draft {scenario_id} not found",
            )

        # Validate each shock against factor registry
        for shock in target_shocks:
            for pt in shock.points:
                validate_factor_shock(shock.factor_id, shock.unit, pt.value)

        now_iso = datetime.now(timezone.utc).isoformat()
        approved = ApprovedScenario.create(
            scenario_id=scenario_id,
            shocks=target_shocks,
            assumptions=target_assumptions,
            approved_at=now_iso,
        )
        self._approved[scenario_id] = approved
        return approved

    def get_approved_scenario(self, scenario_id: str) -> Optional[ApprovedScenario]:
        return self._approved.get(scenario_id)


scenario_service = ScenarioService()
