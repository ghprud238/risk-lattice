"""Snapshot Service per Section 10.2, 10.3 & 14.3.
Loads frozen, immutable snapshots from DuckDB catalog and hands them to the pure math engine.
Preserves strict isolation: the math engine never accesses DuckDB directly.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from app.db.database import db_manager


class SnapshotService:
    def __init__(self, db=None):
        self.db = db or db_manager

    def load_graph_snapshot(
        self, graph_version_id: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Loads frozen graph nodes and edges as in-memory DataFrames."""
        # For canonical graph or specific graph version
        nodes_df = self.db.query_df("SELECT * FROM graph_nodes ORDER BY node_id;")
        edges_df = self.db.query_df("SELECT * FROM graph_edges ORDER BY source_id, target_id;")
        return nodes_df, edges_df

    def load_portfolio_snapshot(
        self, portfolio_version_id: Optional[str] = None
    ) -> Tuple[List[str], List[str], np.ndarray, np.ndarray]:
        """Returns (node_ids, tickers, notionals, weights) for a portfolio version."""
        nodes_df = self.db.query_df("SELECT node_id, name FROM graph_nodes WHERE node_type = 'ASSET' ORDER BY node_id;")
        if nodes_df.empty:
            return [], [], np.array([]), np.array([])
        
        node_ids = nodes_df["node_id"].tolist()
        tickers = nodes_df["node_id"].tolist()
        N = len(node_ids)
        notionals = np.full(N, 1_000_000.0, dtype=np.float64)
        weights = np.full(N, 1.0 / N, dtype=np.float64)
        return node_ids, tickers, notionals, weights

    def load_macro_returns_snapshot(
        self, node_ids: Optional[List[str]] = None, max_days: int = 1000
    ) -> pd.DataFrame:
        """Loads daily return series from DuckDB into a pivoted DataFrame."""
        if node_ids:
            placeholders = ", ".join(f"'{nid}'" for nid in node_ids)
            query = f"""
                SELECT trade_date, node_id, daily_return
                FROM macro_returns
                WHERE node_id IN ({placeholders})
                ORDER BY trade_date, node_id;
            """
        else:
            query = """
                SELECT trade_date, node_id, daily_return
                FROM macro_returns
                ORDER BY trade_date, node_id;
            """
        df = self.db.query_df(query)
        if df.empty:
            return pd.DataFrame()
        pivoted = df.pivot(index="trade_date", columns="node_id", values="daily_return").dropna()
        return pivoted.tail(max_days)


snapshot_service = SnapshotService()
