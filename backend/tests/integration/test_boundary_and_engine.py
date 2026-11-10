"""Boundary and AST Isolation Verification Test per Section 10.2 & 24.1.
Verifies that the math engine (app/engine/) is 100% pure scientific computing
with ZERO imports from external databases (DuckDB), API frameworks (FastAPI),
HTTP clients (requests, httpx), or LLM providers (litellm).
"""

import ast
import glob
import os
import pytest

from app.services.snapshot_service import snapshot_service
from app.engine.propagator import ContagionPropagator, propagate_kernel
from app.engine.risk_metrics import TailRiskEngine
from app.engine.valuation import compute_portfolio_valuation


FORBIDDEN_MODULES = [
    "duckdb",
    "app.db",
    "fastapi",
    "starlette",
    "httpx",
    "requests",
    "litellm",
    "openai",
    "boto3",
]


def test_engine_ast_import_isolation():
    """Scans the Abstract Syntax Tree (AST) of all Python files in app/engine/.
    Asserts zero imports of database, web, network, or LLM packages.
    """
    engine_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../app/engine")
    )
    python_files = glob.glob(os.path.join(engine_dir, "*.py"))
    assert len(python_files) >= 4, f"Expected at least 4 engine modules in {engine_dir}"

    violations = []
    for filepath in python_files:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    for bad in FORBIDDEN_MODULES:
                        if bad in name:
                            violations.append(f"{filename}: 'import {name}' violates isolation rule")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for bad in FORBIDDEN_MODULES:
                    if bad in module:
                        violations.append(f"{filename}: 'from {module} import ...' violates isolation rule")

    assert not violations, f"AST isolation violations found:\n" + "\n".join(violations)


def test_pure_compute_with_frozen_snapshot():
    """Verifies that the pure math engine executes completely using frozen snapshot DataFrames
    without any active DuckDB handle passed to the engine.
    """
    nodes_df, edges_df = snapshot_service.load_graph_snapshot()
    assert not nodes_df.empty
    assert not edges_df.empty

    propagator = ContagionPropagator()
    # Execute pure propagation with explicit snapshot DataFrames
    result = propagator.propagate(
        initial_shock={"NVDA": -0.20, "TSM": -0.25},
        scenario_name="Integration Test Shock",
        nodes_df=nodes_df,
        edges_df=edges_df,
    )

    assert result.total_active_nodes > 0
    assert "NVDA" in result.node_shocks
    assert result.node_shocks["NVDA"].cumulative_shock <= -0.20
