"""Scenario Diffing & A/B Comparison Engine.
PRD Section 16 & Section 24.1 compliant:
- Pure scientific computing with zero database, network, or LLM imports (AST isolated).
- Provides side-by-side comparative analysis of two contagion runs (e.g. Unhedged vs Hedged,
  Taiwan Strait Blockade vs Red Sea Closure, or Base Graph vs Resilient Re-routed Graph).
- Computes delta shocks, delta PnL, delta CVaR, node risk classifications, and divergent transmission paths.
"""

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class NodeDiffStatus(str, Enum):
    AMPLIFIED = "AMPLIFIED"      # Loss worsened in Scenario B
    DE_RISKED = "DE_RISKED"      # Loss reduced/hedged in Scenario B
    UNCHANGED = "UNCHANGED"      # Within noise tolerance (<15% delta)


@dataclass(frozen=True)
class NodeDiffRecord:
    node_id: str
    shock_a: float
    shock_b: float
    delta_shock: float
    pnl_a: float
    pnl_b: float
    delta_pnl: float
    status: NodeDiffStatus
    relative_change_pct: float


@dataclass(frozen=True)
class DivergentEdge:
    source_id: str
    target_id: str
    weight_a: float
    weight_b: float
    delta_weight: float
    description: str


@dataclass(frozen=True)
class ScenarioDiffResult:
    scenario_a_name: str
    scenario_b_name: str
    pnl_a: float
    pnl_b: float
    delta_pnl: float
    cvar_99_a: float
    cvar_99_b: float
    delta_cvar_99: float
    net_improvement_pct: float
    amplified_nodes_count: int
    de_risked_nodes_count: int
    unchanged_nodes_count: int
    node_diffs: Tuple[NodeDiffRecord, ...]
    top_de_risked_nodes: Tuple[NodeDiffRecord, ...]
    top_amplified_nodes: Tuple[NodeDiffRecord, ...]
    divergent_edges: Tuple[DivergentEdge, ...]


class ScenarioDiffEngine:
    """Computes mathematical differential metrics between two stress testing runs."""

    def diff_scenarios(
        self,
        scenario_a_name: str,
        scenario_b_name: str,
        shocks_a: Dict[str, float],
        shocks_b: Dict[str, float],
        positions: Dict[str, float],
        pnl_a: Optional[float] = None,
        pnl_b: Optional[float] = None,
        cvar_a: Optional[float] = None,
        cvar_b: Optional[float] = None,
        edges_a: Optional[Dict[Tuple[str, str], float]] = None,
        edges_b: Optional[Dict[Tuple[str, str], float]] = None,
    ) -> ScenarioDiffResult:
        """Compares Scenario A vs Scenario B with node-by-node attribution."""
        all_nodes = sorted(set(shocks_a.keys()).union(shocks_b.keys()).union(positions.keys()))

        calc_pnl_a = pnl_a if pnl_a is not None else sum(positions.get(n, 0.0) * shocks_a.get(n, 0.0) for n in all_nodes)
        calc_pnl_b = pnl_b if pnl_b is not None else sum(positions.get(n, 0.0) * shocks_b.get(n, 0.0) for n in all_nodes)
        delta_pnl = calc_pnl_b - calc_pnl_a

        calc_cvar_a = cvar_a if cvar_a is not None else abs(calc_pnl_a) * 1.25
        calc_cvar_b = cvar_b if cvar_b is not None else abs(calc_pnl_b) * 1.25
        delta_cvar = calc_cvar_b - calc_cvar_a

        net_improvement_pct = (
            ((calc_cvar_a - calc_cvar_b) / max(1.0, calc_cvar_a)) * 100.0
            if calc_cvar_a > 0
            else 0.0
        )

        node_records: List[NodeDiffRecord] = []
        for n in all_nodes:
            s_a = shocks_a.get(n, 0.0)
            s_b = shocks_b.get(n, 0.0)
            d_s = s_b - s_a

            notional = positions.get(n, 0.0)
            n_pnl_a = notional * s_a
            n_pnl_b = notional * s_b
            d_pnl = n_pnl_b - n_pnl_a

            # Relative change in loss magnitude
            mag_a = abs(s_a)
            mag_b = abs(s_b)
            if mag_a > 1e-4:
                rel_change = ((mag_b - mag_a) / mag_a) * 100.0
            else:
                rel_change = 100.0 if mag_b > 1e-4 else 0.0

            if rel_change < -15.0:
                status = NodeDiffStatus.DE_RISKED
            elif rel_change > 15.0:
                status = NodeDiffStatus.AMPLIFIED
            else:
                status = NodeDiffStatus.UNCHANGED

            node_records.append(
                NodeDiffRecord(
                    node_id=n,
                    shock_a=round(s_a, 4),
                    shock_b=round(s_b, 4),
                    delta_shock=round(d_s, 4),
                    pnl_a=round(n_pnl_a, 2),
                    pnl_b=round(n_pnl_b, 2),
                    delta_pnl=round(d_pnl, 2),
                    status=status,
                    relative_change_pct=round(rel_change, 1),
                )
            )

        # Sort and group records
        de_risked = [r for r in node_records if r.status == NodeDiffStatus.DE_RISKED]
        de_risked.sort(key=lambda x: x.delta_pnl, reverse=True)  # Biggest positive PnL savings first

        amplified = [r for r in node_records if r.status == NodeDiffStatus.AMPLIFIED]
        amplified.sort(key=lambda x: x.delta_pnl)  # Biggest negative PnL loss first

        unchanged = [r for r in node_records if r.status == NodeDiffStatus.UNCHANGED]

        # Edge divergences (if provided)
        divergences: List[DivergentEdge] = []
        if edges_a or edges_b:
            dict_a = edges_a or {}
            dict_b = edges_b or {}
            all_edges = set(dict_a.keys()).union(dict_b.keys())
            for src, tgt in all_edges:
                w_a = dict_a.get((src, tgt), 0.0)
                w_b = dict_b.get((src, tgt), 0.0)
                if abs(w_b - w_a) > 0.05:
                    divergences.append(
                        DivergentEdge(
                            source_id=src,
                            target_id=tgt,
                            weight_a=round(w_a, 3),
                            weight_b=round(w_b, 3),
                            delta_weight=round(w_b - w_a, 3),
                            description=f"Transmission weight from {src} to {tgt} shifted by {(w_b - w_a):+.3f}",
                        )
                    )

        return ScenarioDiffResult(
            scenario_a_name=scenario_a_name,
            scenario_b_name=scenario_b_name,
            pnl_a=round(calc_pnl_a, 2),
            pnl_b=round(calc_pnl_b, 2),
            delta_pnl=round(delta_pnl, 2),
            cvar_99_a=round(calc_cvar_a, 2),
            cvar_99_b=round(calc_cvar_b, 2),
            delta_cvar_99=round(delta_cvar, 2),
            net_improvement_pct=round(net_improvement_pct, 2),
            amplified_nodes_count=len(amplified),
            de_risked_nodes_count=len(de_risked),
            unchanged_nodes_count=len(unchanged),
            node_diffs=tuple(node_records),
            top_de_risked_nodes=tuple(de_risked[:5]),
            top_amplified_nodes=tuple(amplified[:5]),
            divergent_edges=tuple(divergences),
        )
