"""Dynamic Multi-Period Timeline Simulation Engine.
PRD Section 16 & Section 24.1 compliant:
- Pure scientific computing with zero database, network, or LLM imports (AST isolated).
- Simulates propagation waves over time horizons t in [0, 7, 14, 30, 45, 60, 90 days].
- Models dynamic inventory buffer exhaustion, working capital depletion, and cascade escalation.
- Generates chronological milestone alerts and portfolio drawdown trajectories.
"""

from dataclasses import dataclass
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


@dataclass(frozen=True)
class Milestone:
    day: int
    event_type: str  # "SHOCK_TRIGGER" | "BUFFER_EXHAUSTED" | "COVENANT_BREACH" | "SUBSTITUTION_RECOVERY"
    node_id: str
    severity: str  # "INFO" | "WARNING" | "CRITICAL"
    description: str


@dataclass(frozen=True)
class TimelineStep:
    day: int
    cumulative_pnl: float
    drawdown_pct: float
    cvar_99: float
    active_nodes_count: int
    node_shocks: Dict[str, float]
    inventory_levels: Dict[str, float]
    milestones: Tuple[Milestone, ...]


@dataclass(frozen=True)
class TimelineSimulationResult:
    initial_pnl: float
    peak_drawdown_pnl: float
    peak_drawdown_day: int
    peak_drawdown_pct: float
    steps: Tuple[TimelineStep, ...]
    total_milestones: int


class MultiPeriodTimelineEngine:
    """Simulates wave-by-wave contagion progression across discrete time horizons."""

    def __init__(self):
        # Default network topology for semiconductor/hardware supply chain
        self._default_adjacency: Dict[str, List[Tuple[str, float]]] = {
            "TSM": [("NVDA", 0.38), ("AAPL", 0.32), ("AMD", 0.28), ("QCOM", 0.22)],
            "NVDA": [("MSFT", 0.25), ("AMZN", 0.20), ("GOOGL", 0.18)],
            "BALTIC_DRY": [("TSM", 0.15), ("F", 0.25), ("CAT", 0.20)],
            "F": [("APTV", 0.35), ("LEA", 0.30)],
            "FOUNDRY_TW": [("TSM", 0.85), ("UMC", 0.75)],
        }
        self._default_inventory: Dict[str, float] = {
            "TSM": 14.0,
            "NVDA": 21.0,
            "AAPL": 30.0,
            "AMD": 18.0,
            "F": 12.0,
            "APTV": 15.0,
            "MSFT": 45.0,
            "AMZN": 45.0,
            "GOOGL": 60.0,
        }
        self._default_positions: Dict[str, float] = {
            "NVDA": 25_000_000.0,
            "TSM": 20_000_000.0,
            "AAPL": 20_000_000.0,
            "MSFT": 15_000_000.0,
            "F": 10_000_000.0,
            "AMD": 10_000_000.0,
        }

    def simulate(
        self,
        initial_shocks: Dict[str, float],
        portfolio_notional: float = 100_000_000.0,
        time_horizon_days: Optional[List[int]] = None,
        inventory_days: Optional[Dict[str, float]] = None,
        node_positions: Optional[Dict[str, float]] = None,
        adjacency: Optional[Dict[str, List[Tuple[str, float]]]] = None,
    ) -> TimelineSimulationResult:
        """Executes a chronological multi-period simulation."""
        horizons = sorted(time_horizon_days or [0, 7, 14, 30, 45, 60, 90])
        inventory = inventory_days or self._default_inventory
        positions = node_positions or self._default_positions
        graph = adjacency or self._default_adjacency

        steps: List[TimelineStep] = []
        all_milestones: List[Milestone] = []

        # Determine hop distance of each node from initial shock roots via BFS
        hop_distances: Dict[str, int] = {}
        for root in initial_shocks:
            hop_distances[root] = 0

        queue = list(initial_shocks.keys())
        while queue:
            curr = queue.pop(0)
            curr_dist = hop_distances[curr]
            for neighbor, _ in graph.get(curr, []):
                if neighbor not in hop_distances:
                    hop_distances[neighbor] = curr_dist + 1
                    queue.append(neighbor)

        # Track when nodes exhausted their inventory
        exhausted_nodes: set = set()

        for day in horizons:
            current_shocks: Dict[str, float] = {}
            current_inventory: Dict[str, float] = {}
            day_milestones: List[Milestone] = []

            # 1. Day 0 Trigger milestones
            if day == 0:
                for root, shock_val in initial_shocks.items():
                    current_shocks[root] = shock_val
                    current_inventory[root] = inventory.get(root, 30.0)
                    day_milestones.append(
                        Milestone(
                            day=0,
                            event_type="SHOCK_TRIGGER",
                            node_id=root,
                            severity="CRITICAL",
                            description=f"Primary shock triggered: {root} hit with {shock_val * 100.0:.1f}% disruption.",
                        )
                    )

            # 2. Compute state at day t
            # Transmission velocity: 1 hop per 7-10 days
            for node, dist in hop_distances.items():
                if node in initial_shocks:
                    # Root node shock: persists or worsens if unmitigated
                    base_shock = initial_shocks[node]
                    inv_buf = inventory.get(node, 14.0)
                    rem_buf = max(0.0, inv_buf - day)
                    current_inventory[node] = rem_buf

                    # If day exceeds inventory, shock amplifies due to fixed cost bleed
                    if day > inv_buf:
                        escalation = min(1.35, 1.0 + 0.005 * (day - inv_buf))
                        eff_shock = max(-0.95, base_shock * escalation)
                        if node not in exhausted_nodes:
                            exhausted_nodes.add(node)
                            day_milestones.append(
                                Milestone(
                                    day=day,
                                    event_type="BUFFER_EXHAUSTED",
                                    node_id=node,
                                    severity="CRITICAL",
                                    description=f"Buffer depleted: {node} exhausted {inv_buf:.0f}-day safety inventory.",
                                )
                            )
                    else:
                        eff_shock = base_shock
                    current_shocks[node] = round(eff_shock, 4)

                else:
                    # Downstream node: reached after transit delay = dist * 7 days
                    transit_delay = dist * 7
                    if day < transit_delay:
                        # Shock wave has not arrived yet
                        current_shocks[node] = 0.0
                        current_inventory[node] = inventory.get(node, 30.0)
                    else:
                        # Wave arrived at t = transit_delay
                        days_exposed = day - transit_delay
                        inv_buf = inventory.get(node, 30.0)
                        rem_buf = max(0.0, inv_buf - days_exposed)
                        current_inventory[node] = rem_buf

                        # Upstream incoming shock sum
                        parent_shocks = [
                            current_shocks.get(p, 0.0) * w
                            for p, edges in graph.items()
                            for child, w in edges
                            if child == node and p in current_shocks
                        ]
                        raw_shock = min(parent_shocks) if parent_shocks else -0.15

                        if rem_buf > 0:
                            # Partially absorbed by buffer
                            mitigation = (inv_buf - rem_buf) / max(1.0, inv_buf)
                            eff_shock = raw_shock * mitigation
                        else:
                            # Full contagion + liquidity squeeze
                            eff_shock = raw_shock * min(1.30, 1.0 + 0.004 * (days_exposed - inv_buf))
                            if node not in exhausted_nodes:
                                exhausted_nodes.add(node)
                                day_milestones.append(
                                    Milestone(
                                        day=day,
                                        event_type="BUFFER_EXHAUSTED",
                                        node_id=node,
                                        severity="WARNING",
                                        description=f"Downstream disruption: {node} safety stock depleted at day {day}.",
                                    )
                                )

                        current_shocks[node] = round(max(-0.95, eff_shock), 4)

            # Check for substitution / recovery after day 60
            if day >= 60:
                for node in current_shocks:
                    if current_shocks[node] < -0.10:
                        # Secondary supplier qualification begins damping shocks
                        current_shocks[node] = round(current_shocks[node] * 0.90, 4)
                if not any(m.event_type == "SUBSTITUTION_RECOVERY" for m in all_milestones):
                    day_milestones.append(
                        Milestone(
                            day=day,
                            event_type="SUBSTITUTION_RECOVERY",
                            node_id="SYSTEM",
                            severity="INFO",
                            description="Secondary supply routing & production substitution activates (+10% shock recovery).",
                        )
                    )

            # Compute portfolio PnL at day t
            step_pnl = 0.0
            for node, notional in positions.items():
                node_shock = current_shocks.get(node, 0.0)
                step_pnl += notional * node_shock

            drawdown_pct = (step_pnl / max(1.0, portfolio_notional)) * 100.0
            step_cvar_99 = abs(step_pnl) * 1.25

            # Institutional covenant check
            if drawdown_pct <= -15.0 and not any(m.event_type == "COVENANT_BREACH" for m in all_milestones):
                day_milestones.append(
                    Milestone(
                        day=day,
                        event_type="COVENANT_BREACH",
                        node_id="PORTFOLIO",
                        severity="CRITICAL",
                        description=f"Fund Risk Limit Breached: Cumulative drawdown reached {drawdown_pct:.1f}%.",
                    )
                )

            all_milestones.extend(day_milestones)
            active_count = sum(1 for s in current_shocks.values() if abs(s) > 0.01)

            steps.append(
                TimelineStep(
                    day=day,
                    cumulative_pnl=round(step_pnl, 2),
                    drawdown_pct=round(drawdown_pct, 2),
                    cvar_99=round(step_cvar_99, 2),
                    active_nodes_count=active_count,
                    node_shocks=current_shocks,
                    inventory_levels={k: round(v, 1) for k, v in current_inventory.items()},
                    milestones=tuple(day_milestones),
                )
            )

        # Peak drawdown calculation
        peak_idx = int(np.argmin([s.cumulative_pnl for s in steps]))
        peak_step = steps[peak_idx]

        return TimelineSimulationResult(
            initial_pnl=steps[0].cumulative_pnl,
            peak_drawdown_pnl=peak_step.cumulative_pnl,
            peak_drawdown_day=peak_step.day,
            peak_drawdown_pct=peak_step.drawdown_pct,
            steps=tuple(steps),
            total_milestones=len(all_milestones),
        )
