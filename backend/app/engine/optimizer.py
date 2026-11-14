"""Tail-Risk Hedge Optimizer & Reverse Stress Testing Engine.
PRD Section 16 & Section 24.1 compliant:
- Pure scientific computing with zero database, network, or LLM imports (AST isolated).
- Optimal Tail-Risk Hedge Allocation: Solves for the minimum-cost hedging basket
  (Put Options, Single-Name CDS, Freight/Energy Futures) that achieves target risk reduction.
- Reverse Stress Testing: Inverts the propagation kernel to identify the minimal
  plausible macro/supply shock vector that breaches institutional loss thresholds.
"""

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Dict, List, Literal, Optional, Tuple
import numpy as np
from scipy import optimize

from app.engine.instruments import (
    BondPosition,
    CDSPosition,
    EquityPosition,
    OptionPosition,
    OptionType,
    PositionSide,
    evaluate_any_instrument,
)


@dataclass(frozen=True)
class HedgeCandidate:
    candidate_id: str
    target_node: str
    instrument_type: str  # "EQUITY_OPTION" | "CDS" | "INDEX_SHORT"
    side: str  # "BUY" | "SELL" | "SHORT"
    unit_cost_bps: float  # e.g. 350 bps = 3.5% premium
    protection_elasticity: float  # effective Delta or hedge sensitivity
    max_notional: float
    description: str


@dataclass(frozen=True)
class HedgeRecommendation:
    candidate_id: str
    instrument_name: str
    target_node: str
    action: str
    allocated_notional: float
    estimated_cost: float
    pnl_protection: float
    description: str


@dataclass(frozen=True)
class OptimizationResult:
    initial_pnl: float
    hedged_pnl: float
    pnl_improvement: float
    total_hedge_cost: float
    initial_cvar_99: float
    hedged_cvar_99: float
    cvar_reduction_pct: float
    recommendations: Tuple[HedgeRecommendation, ...]
    efficient_frontier: Tuple[Dict[str, float], ...]


@dataclass(frozen=True)
class ReverseStressResult:
    target_loss_pct: float
    achieved_loss_pct: float
    minimal_shocks: Dict[str, float]
    norm_l2: float
    critical_factor: str
    top_vulnerable_nodes: Tuple[Dict[str, Any], ...]
    iterations: int


class TailRiskHedgeOptimizer:
    """Solves for the optimal capital-efficient tail-risk hedge allocation."""

    def __init__(self, candidates: Optional[List[HedgeCandidate]] = None):
        self.candidates = candidates or self._default_candidates()

    def _default_candidates(self) -> List[HedgeCandidate]:
        """Canonical institutional hedging instruments."""
        return [
            HedgeCandidate(
                candidate_id="SOXX_PUT",
                target_node="TSM",
                instrument_type="EQUITY_OPTION",
                side="BUY",
                unit_cost_bps=380.0,  # 3.8% option premium
                protection_elasticity=1.85,  # High gamma convexity on crash
                max_notional=10_000_000.0,
                description="SOXX Semiconductor ETF Out-of-the-Money Put Options (Delta: -0.25)",
            ),
            HedgeCandidate(
                candidate_id="F_CDS_5Y",
                target_node="F",
                instrument_type="CDS",
                side="BUY",
                unit_cost_bps=210.0,  # 210 bps annual spread
                protection_elasticity=1.40,
                max_notional=8_000_000.0,
                description="Ford Motor Credit 5-Year Senior CDS Protection",
            ),
            HedgeCandidate(
                candidate_id="BALTIC_SHORT",
                target_node="BALTIC_DRY",
                instrument_type="INDEX_SHORT",
                side="SHORT",
                unit_cost_bps=120.0,
                protection_elasticity=1.10,
                max_notional=5_000_000.0,
                description="Baltic Dry Index Freight Forward Agreement (FFA) Short Hedge",
            ),
            HedgeCandidate(
                candidate_id="NVDA_PUT",
                target_node="NVDA",
                instrument_type="EQUITY_OPTION",
                side="BUY",
                unit_cost_bps=420.0,
                protection_elasticity=2.10,
                max_notional=10_000_000.0,
                description="NVIDIA 3-Month Out-of-the-Money Put Protection (Delta: -0.22)",
            ),
        ]

    def optimize_hedge(
        self,
        portfolio_notional: float,
        unhedged_pnl: float,
        node_shocks: Dict[str, float],
        budget_limit: float = 500_000.0,
        target_drawdown_pct: Optional[float] = None,
    ) -> OptimizationResult:
        """Solves optimal allocation across hedge candidates subject to budget."""
        M = len(self.candidates)
        costs = np.array([c.unit_cost_bps / 10000.0 for c in self.candidates], dtype=np.float64)
        bounds = [(0.0, c.max_notional) for c in self.candidates]

        # Calculate unit protection payoff for each candidate under current node shocks
        unit_protection = np.zeros(M, dtype=np.float64)
        for j, c in enumerate(self.candidates):
            shock = node_shocks.get(c.target_node, 0.0)
            if shock < 0:
                # Payoff proportional to negative shock * elasticity
                unit_protection[j] = abs(shock) * c.protection_elasticity
            else:
                unit_protection[j] = 0.0

        # If no candidates provide positive protection, allocate nothing
        if np.all(unit_protection <= 0.0):
            return OptimizationResult(
                initial_pnl=round(unhedged_pnl, 2),
                hedged_pnl=round(unhedged_pnl, 2),
                pnl_improvement=0.0,
                total_hedge_cost=0.0,
                initial_cvar_99=round(abs(unhedged_pnl) * 1.25, 2),
                hedged_cvar_99=round(abs(unhedged_pnl) * 1.25, 2),
                cvar_reduction_pct=0.0,
                recommendations=(),
                efficient_frontier=(),
            )

        # Objective: Maximize net protection = sum(x_j * unit_protection[j]) - sum(x_j * costs[j])
        # Minimize: - (net_protection)
        def objective(x: np.ndarray) -> float:
            gross_payoff = float(np.sum(x * unit_protection))
            total_cost = float(np.sum(x * costs))
            return -(gross_payoff - total_cost)

        # Constraint: total_cost <= budget_limit
        def budget_constraint(x: np.ndarray) -> float:
            return budget_limit - float(np.sum(x * costs))

        constraints = [{"type": "ineq", "fun": budget_constraint}]
        x0 = np.array([c.max_notional * 0.25 for c in self.candidates])

        res = optimize.minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 100, "ftol": 1e-6},
        )

        allocated_notionals = np.maximum(0.0, res.x)
        total_hedge_cost = float(np.sum(allocated_notionals * costs))
        total_protection_pnl = float(np.sum(allocated_notionals * unit_protection))

        # Net PnL improvement
        hedged_pnl = unhedged_pnl + total_protection_pnl - total_hedge_cost
        pnl_improvement = hedged_pnl - unhedged_pnl

        # CVaR approximation shift
        initial_cvar_99 = abs(unhedged_pnl) * 1.25
        hedged_cvar_99 = max(0.0, initial_cvar_99 - total_protection_pnl * 0.85 + total_hedge_cost)
        cvar_reduction_pct = (
            (initial_cvar_99 - hedged_cvar_99) / initial_cvar_99 * 100.0
            if initial_cvar_99 > 0
            else 0.0
        )

        recommendations: List[HedgeRecommendation] = []
        for j, c in enumerate(self.candidates):
            notional = float(allocated_notionals[j])
            if notional > 10_000.0:  # Skip trivial allocations
                cost = notional * costs[j]
                payoff = notional * unit_protection[j]
                recommendations.append(
                    HedgeRecommendation(
                        candidate_id=c.candidate_id,
                        instrument_name=c.description,
                        target_node=c.target_node,
                        action=c.side,
                        allocated_notional=round(notional, 2),
                        estimated_cost=round(cost, 2),
                        pnl_protection=round(payoff, 2),
                        description=f"Hedges {c.target_node} contagion via {c.instrument_type}",
                    )
                )

        # Efficient Frontier: sample 5 budget points from 10% to 150% of budget
        frontier: List[Dict[str, float]] = []
        for b_frac in [0.2, 0.5, 0.8, 1.0, 1.5]:
            sub_budget = budget_limit * b_frac
            sub_alloc = np.minimum(
                allocated_notionals * (sub_budget / max(1.0, total_hedge_cost)),
                [c.max_notional for c in self.candidates],
            )
            sub_cost = float(np.sum(sub_alloc * costs))
            sub_prot = float(np.sum(sub_alloc * unit_protection))
            frontier.append({
                "budget": round(sub_cost, 2),
                "protection_pnl": round(sub_prot, 2),
                "cvar_reduction_pct": round(min(90.0, (sub_prot / max(1.0, initial_cvar_99)) * 100.0), 1),
            })

        return OptimizationResult(
            initial_pnl=round(unhedged_pnl, 2),
            hedged_pnl=round(hedged_pnl, 2),
            pnl_improvement=round(pnl_improvement, 2),
            total_hedge_cost=round(total_hedge_cost, 2),
            initial_cvar_99=round(initial_cvar_99, 2),
            hedged_cvar_99=round(hedged_cvar_99, 2),
            cvar_reduction_pct=round(cvar_reduction_pct, 2),
            recommendations=tuple(recommendations),
            efficient_frontier=tuple(frontier),
        )


class ReverseStressTester:
    """Inverts the stress tester to find the minimal shock vector causing portfolio breach."""

    def __init__(self, key_factors: Optional[List[str]] = None):
        self.factors = key_factors or [
            "FOUNDRY_TW",
            "BALTIC_DRY",
            "BRENT_CRUDE",
            "SOFR_SPREAD",
            "HY_OAS",
            "CANAL_TRANSIT",
            "CLOUD_OUTAGE_SEV",
        ]

    def find_breaking_point(
        self,
        portfolio_notional: float,
        target_loss_pct: float = 0.20,  # e.g. 20% loss threshold
        factor_sensitivities: Optional[Dict[str, float]] = None,
    ) -> ReverseStressResult:
        """Solves min ||F||_2 subject to Portfolio_Loss(F) >= target_loss_pct."""
        sens = factor_sensitivities or {
            "FOUNDRY_TW": 0.45,
            "BALTIC_DRY": 0.30,
            "BRENT_CRUDE": 0.25,
            "SOFR_SPREAD": 0.35,
            "HY_OAS": 0.40,
            "CANAL_TRANSIT": 0.28,
            "CLOUD_OUTAGE_SEV": 0.20,
        }

        K = len(self.factors)
        beta_vec = np.array([sens.get(f, 0.25) for f in self.factors], dtype=np.float64)

        # Objective: minimize L2 norm = sum(f_k^2)
        def objective(f: np.ndarray) -> float:
            return float(np.sum(f ** 2))

        # Constraint: sum(beta_k * f_k) >= target_loss_pct
        def loss_constraint(f: np.ndarray) -> float:
            return float(np.sum(beta_vec * f)) - target_loss_pct

        # Factor bounds (fractional drops [0, 0.8])
        bounds = [(0.0, 0.85) for _ in self.factors]
        constraints = [{"type": "ineq", "fun": loss_constraint}]
        f0 = np.ones(K) * (target_loss_pct / np.sum(beta_vec))

        res = optimize.minimize(
            objective,
            f0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 100, "ftol": 1e-6},
        )

        opt_f = np.maximum(0.0, res.x)
        achieved_loss = float(np.sum(beta_vec * opt_f))
        norm_l2 = float(np.linalg.norm(opt_f))

        shocks_dict: Dict[str, float] = {}
        for k, factor_name in enumerate(self.factors):
            shocks_dict[factor_name] = round(-float(opt_f[k]), 4)

        # Identify critical factor (highest contribution to target loss)
        contributions = beta_vec * opt_f
        crit_idx = int(np.argmax(contributions))
        critical_factor = self.factors[crit_idx]

        vulnerable_nodes = [
            {"factor": f, "shock": shocks_dict[f], "loss_contribution_pct": round(float(contributions[i] / max(1e-4, achieved_loss) * 100.0), 1)}
            for i, f in enumerate(self.factors)
            if abs(shocks_dict[f]) > 0.01
        ]
        vulnerable_nodes.sort(key=lambda x: x["loss_contribution_pct"], reverse=True)

        return ReverseStressResult(
            target_loss_pct=target_loss_pct,
            achieved_loss_pct=round(achieved_loss, 4),
            minimal_shocks=shocks_dict,
            norm_l2=round(norm_l2, 4),
            critical_factor=critical_factor,
            top_vulnerable_nodes=tuple(vulnerable_nodes),
            iterations=int(res.nit),
        )
