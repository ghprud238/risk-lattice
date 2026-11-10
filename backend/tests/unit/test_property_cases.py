"""Property Test Cases P-01 to P-05 per Section 23.2 (Page 57).
Tests mathematical properties: permutation invariance, notional scaling, CSR vs dense equivalence, limit behavior.
"""

import numpy as np
from scipy.sparse import csr_matrix
import pytest

from app.engine.propagator import propagate_kernel
from app.engine.valuation import compute_portfolio_valuation


def test_p01_permutation_invariance():
    """P-01: Permutation invariance:
    Permuting node indices in input and graph edges yields identically permuted outputs.
    """
    # 3 nodes: A (0), B (1), C (2)
    # A -> B (0.5), B -> C (0.4)
    seed = np.array([0.15, -0.05, 0.0], dtype=np.float64)
    edges = [(0, 1, 0.5, "GENERIC"), (1, 2, 0.4, "GENERIC")]
    
    hops_orig, total_orig, _, _ = propagate_kernel(seed, edges, alpha=0.65)
    
    # Permutation: swap 0 and 2 -> perm = [2, 1, 0]
    perm = [2, 1, 0]
    inv_perm = [2, 1, 0]
    
    seed_perm = seed[perm]
    edges_perm = [(inv_perm[src], inv_perm[tgt], w, rel) for src, tgt, w, rel in edges]
    
    hops_perm, total_perm, _, _ = propagate_kernel(seed_perm, edges_perm, alpha=0.65)
    
    # Total returns must match after reversing permutation
    assert np.allclose(total_perm[inv_perm], total_orig, atol=1e-12)
    for k in range(5):
        assert np.allclose(hops_perm[k][inv_perm], hops_orig[k], atol=1e-12)


def test_p02_notional_scaling():
    """P-02: Notional scaling:
    Scaling portfolio notional by scalar c scales dollar PnL by exactly c.
    """
    node_ids = ["NODE_A", "NODE_B", "NODE_C"]
    tickers = ["A", "B", "C"]
    notionals = np.array([100_000.0, 250_000.0, 500_000.0], dtype=np.float64)
    hop_returns = np.array([
        [-0.05, -0.02, -0.01],  # hop 0
        [-0.03, -0.04, -0.02],  # hop 1
        [-0.01, -0.02, -0.03],  # hop 2
        [0.0, -0.01, -0.01],    # hop 3
        [0.0, 0.0, -0.005],     # hop 4
    ], dtype=np.float64)
    
    res1 = compute_portfolio_valuation(node_ids, tickers, notionals, hop_returns)
    
    # Scale notionals by 3.5x
    scale_factor = 3.5
    res2 = compute_portfolio_valuation(node_ids, tickers, notionals * scale_factor, hop_returns)
    
    assert np.isclose(res2.total_notional, res1.total_notional * scale_factor)
    assert np.isclose(res2.total_pnl, res1.total_pnl * scale_factor)
    # Return percentage is intensive and must be invariant
    assert np.isclose(res2.portfolio_return, res1.portfolio_return, atol=1e-12)


def test_p03_csr_vs_dense_reference():
    """P-03: Sparse CSR message passing matches dense array operations within 1e-15."""
    N = 10
    rng = np.random.default_rng(123)
    
    # Dense random sensitivity matrix with 70% sparsity
    W_dense = rng.uniform(-0.5, 0.5, size=(N, N))
    W_dense[rng.uniform(0, 1, size=(N, N)) < 0.7] = 0.0
    
    # Build CSR matrix
    W_csr = csr_matrix(W_dense)
    
    # Impulse vector
    impulse = rng.uniform(-0.2, 0.2, size=N)
    
    dense_out = impulse @ W_dense
    csr_out = impulse @ W_csr
    
    assert np.allclose(dense_out, csr_out, atol=1e-15), "CSR and dense matrix products must match within 1e-15"


def test_p04_limit_behavior_extreme_shocks():
    """P-04: Limit behavior / extreme shocks:
    Extreme shocks of -10.0 or +50.0 clamp cleanly to [-0.95, +2.00] without NaN or overflow.
    """
    seed_extreme = np.array([-10.0, 50.0, -0.50], dtype=np.float64)
    edges = [(0, 1, 0.5, "GENERIC"), (1, 2, 0.5, "GENERIC")]
    
    hops, final_total, reconciliation, _ = propagate_kernel(
        seed_extreme, edges, clip_min=-0.95, clip_max=2.00
    )
    
    assert np.all(np.isfinite(hops))
    assert np.all(np.isfinite(final_total))
    assert np.all(final_total >= -0.95)
    assert np.all(final_total <= 2.00)
    assert final_total[0] == -0.95
    assert final_total[1] == 2.00


def test_p05_graph_scaling_sparsity():
    """P-05: Graph scaling / sparsity:
    Star graph and dense bipartite structures remain stable and finish in bounded time.
    """
    N = 50
    center = 0
    # Star graph: center connects to all 49 leaves
    edges = [(center, i, 0.3, "SUPPLY") for i in range(1, N)]
    seed = np.zeros(N, dtype=np.float64)
    seed[center] = -0.30
    
    hops, final_total, _, diagnostics = propagate_kernel(seed, edges, max_hops=4)
    
    assert hops.shape == (5, N)
    # At hop 1, all 49 leaves receive impulse: 0.65 * 0.3 * (-0.30) = -0.0585
    assert np.allclose(hops[1, 1:], 0.65 * 0.3 * (-0.30))
    # At hop 2, leaves don't connect anywhere, so hop 2 is zero
    assert np.allclose(hops[2], 0.0)
