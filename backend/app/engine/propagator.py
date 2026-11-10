"""
Deterministic Multi-Hop Contagion Propagator.
PRD Section 4.1:
- Damped sparse-matrix message passing across up to 4 hops
- Hop iteration: Delta s_v^(k) = alpha^(k-1) * sum_u(W_uv * Delta s_u^(k-1)) * (1 - sigma_v) * lambda_v
- Non-linear balance sheet distress multiplier lambda_v
- Cumulative clamped node shock: S_v = clip(sum_{k=0}^4 Delta s_v^(k), -0.95, +1.50)
- Fixed convergence tolerance (10^-4), bit-for-bit identical reproducibility
"""
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from app.engine.calibrator import EdgeCalibrator


class NodeShockResult(BaseModel):
    node_id: str
    node_type: str
    name: str
    sector: str
    hop0: float
    hop1: float
    hop2: float
    hop3: float
    hop4: float
    cumulative_shock: float
    order1_direct: float
    order2_tier1: float
    order3_4_network: float
    distress_multiplier: float


class ContagionSimulationResult(BaseModel):
    scenario_name: str
    node_shocks: Dict[str, NodeShockResult]
    portfolio_pnl: Dict[str, float]
    critical_paths: List[List[str]]
    total_active_nodes: int


class ContagionPropagator:
    def __init__(
        self,
        alpha_decay: float = 0.65,
        max_hops: int = 4,
        tolerance: float = 1e-4,
        calibrator: Optional[EdgeCalibrator] = None
    ):
        self.alpha_decay = alpha_decay
        self.max_hops = max_hops
        self.tolerance = tolerance
        self.calibrator = calibrator or EdgeCalibrator()

    def compute_distress_multipliers(self, nodes_df: pd.DataFrame) -> np.ndarray:
        """
        Computes balance sheet distress multiplier lambda_v:
        If node v is corporate asset with NetDebt/EBITDA > 3.0 or InterestCoverage < 1.5,
        lambda_v = 1 + 0.35 * max(0, NetDebt/EBITDA - 3.0); otherwise lambda_v = 1.0.
        """
        N = len(nodes_df)
        lambdas = np.ones(N, dtype=np.float64)

        for i, (_, row) in enumerate(nodes_df.iterrows()):
            node_type = row.get("node_type", "")
            net_debt_ebitda = float(row.get("net_debt_ebitda", 0.0) or 0.0)
            int_coverage = float(row.get("int_coverage", 5.0) or 5.0)

            # Applies to corporate assets and suppliers with debt metrics
            if node_type in ("ASSET", "SUPPLIER"):
                if net_debt_ebitda > 3.0 or int_coverage < 1.5:
                    excess_leverage = max(0.0, net_debt_ebitda - 3.0)
                    lambdas[i] = 1.0 + 0.35 * excess_leverage
                else:
                    lambdas[i] = 1.0
            else:
                lambdas[i] = 1.0

        return lambdas

    def propagate(
        self,
        initial_shock: Dict[str, float],
        scenario_name: str = "Custom Scenario",
        portfolio_weights: Optional[Dict[str, float]] = None,
        nodes_df: Optional[pd.DataFrame] = None,
        edges_df: Optional[pd.DataFrame] = None
    ) -> ContagionSimulationResult:
        """
        Executes bit-exact 4-hop damped propagation.
        initial_shock: mapping of node_id -> shock value clamped to [-0.95, +2.00]
        """
        if nodes_df is None or edges_df is None:
            nodes_df, edges_df = self.calibrator.load_graph_data()

        W, _, node_to_idx, idx_to_node = self.calibrator.build_sensitivity_matrix(nodes_df, edges_df)
        N = len(node_to_idx)

        # Build initial shock vector s^(0)
        s0 = np.zeros(N, dtype=np.float64)
        for nid, val in initial_shock.items():
            if nid in node_to_idx:
                # Clamp initial shocks to [-0.95, 2.00]
                s0[node_to_idx[nid]] = float(np.clip(val, -0.95, 2.00))

        # Substitutability vector sigma_v clamped to [0.0, 0.8]
        substitutabilities = np.zeros(N, dtype=np.float64)
        for _, row in nodes_df.iterrows():
            idx = node_to_idx[row["node_id"]]
            substitutabilities[idx] = float(np.clip(row.get("substitutability", 0.3), 0.0, 0.8))

        # Distress multipliers lambda_v
        lambdas = self.compute_distress_multipliers(nodes_df)

        # Storage for hop impulses: Delta s^(k) of shape (max_hops + 1, N)
        delta_s = np.zeros((self.max_hops + 1, N), dtype=np.float64)
        delta_s[0] = s0

        # Hop iteration k = 1, 2, 3, 4
        # Delta s_v^(k) = alpha^(k-1) * sum_u (W_uv * Delta s_u^(k-1)) * (1 - sigma_v) * lambda_v
        for k in range(1, self.max_hops + 1):
            prev_impulse = delta_s[k - 1]
            # Matrix multiplication: prev_impulse @ W gives incoming sum_u (W_uv * prev_impulse_u)
            incoming = np.dot(prev_impulse, W)

            decay = self.alpha_decay ** (k - 1)
            hop_k = np.zeros(N, dtype=np.float64)

            for v in range(N):
                raw_v = incoming[v]
                if abs(raw_v) < self.tolerance:
                    hop_k[v] = 0.0
                    continue

                sub_factor = 1.0 - substitutabilities[v]
                # Non-linear distress multiplier: amplifies negative shocks
                multiplier = lambdas[v] if raw_v < 0 else 1.0
                hop_k[v] = decay * raw_v * sub_factor * multiplier

            delta_s[k] = hop_k

        # Cumulative shock: S_v = clip(sum_{k=0}^4 Delta s_v^(k), -0.95, +1.50)
        cumulative_raw = np.sum(delta_s, axis=0)
        cumulative_clamped = np.clip(cumulative_raw, -0.95, 1.50)

        # Order decomposition
        # Order 1 (Direct Macro / Initial Shock + Hop 1)
        order1 = delta_s[0] + delta_s[1]
        # Order 2 (Tier 1 Supplier/Customer: Hop 2)
        order2 = delta_s[2]
        # Order 3 & 4 (Network Contagion: Hop 3 + Hop 4)
        order3_4 = delta_s[3] + delta_s[4]

        # Build node shock result dictionary
        node_results: Dict[str, NodeShockResult] = {}
        for _, row in nodes_df.iterrows():
            nid = row["node_id"]
            i = node_to_idx[nid]
            node_results[nid] = NodeShockResult(
                node_id=nid,
                node_type=row.get("node_type", "ASSET"),
                name=row.get("name", nid),
                sector=row.get("sector", "Unknown"),
                hop0=round(float(delta_s[0, i]), 5),
                hop1=round(float(delta_s[1, i]), 5),
                hop2=round(float(delta_s[2, i]), 5),
                hop3=round(float(delta_s[3, i]), 5),
                hop4=round(float(delta_s[4, i]), 5),
                cumulative_shock=round(float(cumulative_clamped[i]), 5),
                order1_direct=round(float(order1[i]), 5),
                order2_tier1=round(float(order2[i]), 5),
                order3_4_network=round(float(order3_4[i]), 5),
                distress_multiplier=round(float(lambdas[i]), 3),
            )

        # Compute portfolio PnL waterfall
        # Default equal weighting across public equities if portfolio_weights not provided
        if not portfolio_weights:
            equity_nodes = nodes_df[nodes_df["node_type"] == "ASSET"]["node_id"].tolist()
            w = 1.0 / len(equity_nodes) if equity_nodes else 0.0
            portfolio_weights = {nid: w for nid in equity_nodes}

        pnl_hop1 = 0.0
        pnl_hop2 = 0.0
        pnl_hop3_4 = 0.0
        pnl_total = 0.0

        for nid, weight in portfolio_weights.items():
            if nid in node_results:
                res = node_results[nid]
                pnl_hop1 += weight * res.order1_direct
                pnl_hop2 += weight * res.order2_tier1
                pnl_hop3_4 += weight * res.order3_4_network
                pnl_total += weight * res.cumulative_shock

        portfolio_pnl = {
            "hop1_pnl": round(float(pnl_hop1), 5),
            "hop2_pnl": round(float(pnl_hop2), 5),
            "hop3_4_pnl": round(float(pnl_hop3_4), 5),
            "total_pnl": round(float(pnl_total), 5),
        }

        # Tracing critical contagion paths
        critical_paths = self._find_critical_paths(delta_s, W, node_to_idx, idx_to_node)

        active_count = int(np.sum(np.abs(cumulative_clamped) > 0.005))

        return ContagionSimulationResult(
            scenario_name=scenario_name,
            node_shocks=node_results,
            portfolio_pnl=portfolio_pnl,
            critical_paths=critical_paths,
            total_active_nodes=active_count,
        )

    def _find_critical_paths(
        self,
        delta_s: np.ndarray,
        W: np.ndarray,
        node_to_idx: Dict[str, int],
        idx_to_node: Dict[int, str],
        top_k: int = 5
    ) -> List[List[str]]:
        """Identifies top multi-hop chains with strongest shock transmission."""
        paths = []
        # Find top source nodes at hop 0 / hop 1
        source_indices = np.argsort(np.abs(delta_s[0]))[::-1]
        for src in source_indices:
            if abs(delta_s[0, src]) < 0.05:
                continue
            path = [idx_to_node[src]]
            curr = src
            for hop in range(1, min(self.max_hops + 1, 4)):
                downstream = W[curr, :]
                weighted_impacts = downstream * delta_s[hop]
                if len(weighted_impacts) == 0 or np.max(np.abs(weighted_impacts)) < 0.01:
                    break
                next_node = int(np.argmax(np.abs(weighted_impacts)))
                path.append(idx_to_node[next_node])
                curr = next_node
            if len(path) > 1:
                paths.append(path)
            if len(paths) >= top_k:
                break
        return paths


def propagate_kernel(
    seed: np.ndarray,
    edges: List[Tuple[int, int, float, str]],
    substitution: Optional[np.ndarray] = None,
    distress: Optional[np.ndarray] = None,
    max_hops: int = 4,
    alpha: float = 0.65,
    clip_min: float = -0.95,
    clip_max: float = 2.00,
    tolerance: float = 1e-4,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[Dict[str, Any]]]:
    """
    Pure deterministic analytical propagation kernel per Section 9, 16.2 & 23.1.
    
    Each hop computes one incremental impulse using alpha=0.65 applied once per edge:
        c = alpha * weight * impulse[edge.source]
    Relation filtering:
        If edge.relation == 'SUPPLY': c *= (1.0 - substitution[edge.target])
    Signed distress amplification:
        If c < 0.0: c *= distress[edge.target]
    Cumulative clamping:
        raw_total = sum(hops)
        final_total = clip(raw_total, clip_min, clip_max)
        reconciliation = final_total - raw_total
    """
    N = len(seed)
    if substitution is None:
        substitution = np.zeros(N, dtype=np.float64)
    if distress is None:
        distress = np.ones(N, dtype=np.float64)

    impulse = seed.copy().astype(np.float64)
    hops = [impulse.copy()]
    diagnostics = []

    for k in range(1, max_hops + 1):
        next_impulse = np.zeros(N, dtype=np.float64)
        visited_targets = set()
        for src, tgt, weight, relation in edges:
            if abs(impulse[src]) < tolerance:
                continue
            c = alpha * weight * impulse[src]
            if relation == "SUPPLY":
                c *= (1.0 - substitution[tgt])
            if c < 0.0:
                c *= distress[tgt]
            next_impulse[tgt] += c
            visited_targets.add(tgt)

        if not np.all(np.isfinite(next_impulse)):
            raise ValueError("Non-finite values detected in propagation impulse")

        hops.append(next_impulse.copy())
        diagnostics.append({
            "hop": k,
            "active_nodes": int(np.sum(np.abs(next_impulse) >= tolerance)),
            "max_impulse": float(np.max(np.abs(next_impulse))) if len(next_impulse) else 0.0,
            "visited_count": len(visited_targets),
        })
        impulse = next_impulse

    hops_arr = np.array(hops)
    raw_total = np.sum(hops_arr, axis=0)
    final_total = np.clip(raw_total, clip_min, clip_max)
    reconciliation = final_total - raw_total

    return hops_arr, final_total, reconciliation, diagnostics

