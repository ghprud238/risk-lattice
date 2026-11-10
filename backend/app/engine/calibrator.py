"""
Econometric Edge Weight Calibrator.
PRD Section 4 & 5:
- Huber robust regression on daily return series to estimate factor betas
- Scaling of supply-chain weights by substitutability and leverage
- 100% deterministic Python/NumPy math; zero LLM involvement in numeric weights
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.linear_model import HuberRegressor

from app.db.database import db_manager


class EdgeCalibrator:
    def __init__(self, db=None):
        self.db = db or db_manager

    def load_graph_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Loads nodes and structural edges from DuckDB."""
        nodes_df = self.db.query_df("SELECT * FROM graph_nodes ORDER BY node_id;")
        edges_df = self.db.query_df("SELECT * FROM graph_edges ORDER BY source_id, target_id;")
        return nodes_df, edges_df

    def calibrate_huber_beta(
        self,
        target_node: str,
        factor_nodes: List[str],
        regime_filter: Optional[str] = None,
        max_samples: int = 1000
    ) -> Dict[str, float]:
        """
        Runs Huber robust regression to estimate sensitivities (betas)
        of target_node against factor_nodes.
        Deterministic and outlier-resistant.
        """
        where_clause = ""
        if regime_filter:
            where_clause = f"AND regime_tag = '{regime_filter}'"

        all_nodes = [target_node] + factor_nodes
        placeholders = ", ".join(f"'{nid}'" for nid in all_nodes)
        query = f"""
            SELECT trade_date, node_id, daily_return
            FROM macro_returns
            WHERE node_id IN ({placeholders}) {where_clause}
            ORDER BY trade_date, node_id;
        """
        df = self.db.query_df(query)
        if df.empty:
            return {f: 0.0 for f in factor_nodes}

        pivoted = df.pivot(index="trade_date", columns="node_id", values="daily_return").dropna()
        if len(pivoted) < 20 or target_node not in pivoted.columns:
            return {f: 0.0 for f in factor_nodes}

        # Keep only factors present in pivoted data
        valid_factors = [f for f in factor_nodes if f in pivoted.columns]
        if not valid_factors:
            return {f: 0.0 for f in factor_nodes}

        X = pivoted[valid_factors].values[-max_samples:]
        y = pivoted[target_node].values[-max_samples:]

        try:
            huber = HuberRegressor(epsilon=1.35, max_iter=200, alpha=0.0001)
            huber.fit(X, y)
            betas = {f: float(np.clip(coef, -1.0, 1.0)) for f, coef in zip(valid_factors, huber.coef_)}
            # Fill missing factors if any
            for f in factor_nodes:
                if f not in betas:
                    betas[f] = 0.0
            return betas
        except Exception:
            # Fallback to bounded OLS covariance
            betas = {}
            var_y = np.var(y) + 1e-8
            for i, f in enumerate(valid_factors):
                cov = np.cov(X[:, i], y)[0, 1]
                var_x = np.var(X[:, i]) + 1e-8
                beta = cov / var_x
                betas[f] = float(np.clip(beta, -1.0, 1.0))
            for f in factor_nodes:
                if f not in betas:
                    betas[f] = 0.0
            return betas

    def build_sensitivity_matrix(
        self,
        nodes_df: Optional[pd.DataFrame] = None,
        edges_df: Optional[pd.DataFrame] = None
    ) -> Tuple[np.ndarray, csr_matrix, Dict[str, int], Dict[int, str]]:
        """
        Builds the N x N sensitivity matrix W where W[u, v] represents
        the impulse sensitivity from source node u to target node v.
        Returns:
            dense W, csr_matrix W, node_to_idx mapping, idx_to_node mapping
        """
        if nodes_df is None or edges_df is None:
            nodes_df, edges_df = self.load_graph_data()

        node_ids = nodes_df["node_id"].tolist()
        N = len(node_ids)
        node_to_idx = {nid: i for i, nid in enumerate(node_ids)}
        idx_to_node = {i: nid for i, nid in enumerate(node_ids)}

        W = np.zeros((N, N), dtype=np.float64)

        for _, row in edges_df.iterrows():
            src = row["source_id"]
            tgt = row["target_id"]
            if src in node_to_idx and tgt in node_to_idx:
                u = node_to_idx[src]
                v = node_to_idx[tgt]
                # Enforce bound ABS(base_weight) <= 1.0
                weight = float(np.clip(row["base_weight"], -1.0, 1.0))
                W[u, v] = weight

        sparse_W = csr_matrix(W)
        return W, sparse_W, node_to_idx, idx_to_node
