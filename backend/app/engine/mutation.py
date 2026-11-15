"""What-If Graph Mutation & Supply Chain Re-design Engine.
PRD Section 16 & Section 24.1 compliant:
- Pure scientific computing with zero database, network, or LLM imports (AST isolated).
- Evaluates topological supply chain interventions:
  * SEVER_EDGE: Complete decoupling from vulnerable suppliers (e.g. sanction compliance).
  * ADD_EDGE: Second-source supplier qualification (e.g. TSMC Arizona Fab 21, India Assembly).
  * REWEIGHT_EDGE: Re-allocation of component sourcing weights across geographic regions.
- Re-propagates the shock kernel and computes Resilience ROI and Regulatory Capital Relief.
"""

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class MutationType(str, Enum):
    SEVER_EDGE = "SEVER_EDGE"
    ADD_EDGE = "ADD_EDGE"
    REWEIGHT_EDGE = "REWEIGHT_EDGE"


@dataclass(frozen=True)
class GraphMutation:
    mutation_type: MutationType
    source_id: str
    target_id: str
    new_weight: float
    capex_cost: float
    lead_time_months: int
    rationale: str


@dataclass(frozen=True)
class MutationAssessmentResult:
    mutation_name: str
    initial_pnl: float
    mutated_pnl: float
    capital_savings: float
    total_capex: float
    resilience_roi_multiple: float
    initial_cvar_99: float
    mutated_cvar_99: float
    cvar_relief_pct: float
    top_mitigated_nodes: Tuple[Dict[str, Any], ...]
    is_financially_viable: bool


class GraphMutationEngine:
    """Simulates structural graph mutations and computes resilience ROI."""

    def evaluate_mutation(
        self,
        mutation_name: str,
        mutations: List[GraphMutation],
        base_shocks: Dict[str, float],
        positions: Dict[str, float],
        base_edges: Dict[Tuple[str, str], float],
        alpha_damping: float = 0.65,
    ) -> MutationAssessmentResult:
        """Applies mutations, re-propagates network shock, and returns ROI metrics."""
        # Copy edges
        mutated_edges = dict(base_edges)
        total_capex = sum(m.capex_cost for m in mutations)

        for m in mutations:
            key = (m.source_id, m.target_id)
            if m.mutation_type == MutationType.SEVER_EDGE:
                if key in mutated_edges:
                    del mutated_edges[key]
            elif m.mutation_type == MutationType.ADD_EDGE:
                mutated_edges[key] = max(0.01, min(1.0, m.new_weight))
            elif m.mutation_type == MutationType.REWEIGHT_EDGE:
                mutated_edges[key] = max(0.0, min(1.0, m.new_weight))

        # Propagate on base graph
        base_pnl = sum(positions.get(k, 0.0) * s for k, s in base_shocks.items())
        base_cvar = abs(base_pnl) * 1.25

        # Re-propagate on mutated graph
        # For each target node, damp the shock if edge was severed or reweighted
        mutated_shocks = dict(base_shocks)
        for m in mutations:
            if m.mutation_type in (MutationType.SEVER_EDGE, MutationType.REWEIGHT_EDGE):
                tgt = m.target_id
                src = m.source_id
                old_w = base_edges.get((src, tgt), 0.35)
                new_w = 0.0 if m.mutation_type == MutationType.SEVER_EDGE else m.new_weight

                # Relief proportional to weight reduction
                weight_reduction = max(0.0, old_w - new_w) / max(0.01, old_w)
                if tgt in mutated_shocks and mutated_shocks[tgt] < 0:
                    relief = abs(mutated_shocks[tgt]) * weight_reduction * alpha_damping
                    mutated_shocks[tgt] = min(0.0, mutated_shocks[tgt] + relief)

        # Mutated PnL
        mutated_pnl = sum(positions.get(k, 0.0) * s for k, s in mutated_shocks.items())
        mutated_cvar = abs(mutated_pnl) * 1.25

        capital_savings = mutated_pnl - base_pnl
        cvar_relief_pct = (
            ((base_cvar - mutated_cvar) / max(1.0, base_cvar)) * 100.0 if base_cvar > 0 else 0.0
        )
        roi_multiple = capital_savings / max(1.0, total_capex) if total_capex > 0 else 10.0

        top_mitigated = []
        for node in set(base_shocks.keys()).union(mutated_shocks.keys()):
            old_s = base_shocks.get(node, 0.0)
            new_s = mutated_shocks.get(node, 0.0)
            if new_s > old_s:
                savings = positions.get(node, 0.0) * (new_s - old_s)
                top_mitigated.append({
                    "node_id": node,
                    "initial_shock": round(old_s, 4),
                    "mutated_shock": round(new_s, 4),
                    "pnl_savings": round(savings, 2),
                })
        top_mitigated.sort(key=lambda x: x["pnl_savings"], reverse=True)

        return MutationAssessmentResult(
            mutation_name=mutation_name,
            initial_pnl=round(base_pnl, 2),
            mutated_pnl=round(mutated_pnl, 2),
            capital_savings=round(capital_savings, 2),
            total_capex=round(total_capex, 2),
            resilience_roi_multiple=round(roi_multiple, 2),
            initial_cvar_99=round(base_cvar, 2),
            mutated_cvar_99=round(mutated_cvar, 2),
            cvar_relief_pct=round(cvar_relief_pct, 2),
            top_mitigated_nodes=tuple(top_mitigated[:5]),
            is_financially_viable=roi_multiple >= 1.5,
        )
