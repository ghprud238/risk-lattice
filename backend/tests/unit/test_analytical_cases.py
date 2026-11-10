"""Analytical Numerical Test Cases N-01 to N-12 per Section 23.1 (Page 56).
Pure analytical fixtures testing mathematical invariants, sign conservation, orientation, and edge semantics.
"""

import numpy as np
import pytest

from app.domain.errors import ContagionDomainException, FailureCode
from app.domain.factor_registry import validate_factor_shock
from app.engine.propagator import propagate_kernel
from app.engine.valuation import compound_return


def test_n01_orientation():
    """N-01: Two nodes; W[target, source]. Only intended target responds; transpose detected."""
    # Node 0 (source), Node 1 (target)
    # Edge: 0 -> 1 with weight 0.5
    seed = np.array([0.10, 0.0], dtype=np.float64)
    edges = [(0, 1, 0.5, "GENERIC")]
    
    hops, final_total, reconciliation, _ = propagate_kernel(seed, edges, alpha=0.65, max_hops=4)
    
    # Target (Node 1) should receive impulse at hop 1: 0.65 * 0.5 * 0.10 = 0.0325
    assert np.isclose(hops[1, 1], 0.0325), f"Target node 1 expected 0.0325, got {hops[1, 1]}"
    # Source (Node 0) must NOT receive any incoming impulse (downstream increment is zero)
    assert np.isclose(hops[1, 0], 0.0), f"Source node 0 should receive 0.0, got {hops[1, 0]}"
    assert np.isclose(final_total[1], 0.0325)


def test_n02_zero_graph():
    """N-02: Nonzero seed, no edges, K=4. Hop0 only; all downstream increments exactly zero."""
    seed = np.array([0.15, -0.20, 0.05], dtype=np.float64)
    edges = []
    
    hops, final_total, reconciliation, _ = propagate_kernel(seed, edges, max_hops=4)
    
    assert np.allclose(hops[0], seed)
    for k in range(1, 5):
        assert np.allclose(hops[k], 0.0), f"Hop {k} must be exactly zero for empty graph"
    assert np.allclose(final_total, seed)
    assert np.allclose(reconciliation, 0.0)


def test_n03_zero_shock():
    """N-03: Zero seed; residual disabled. All deterministic PnL / adjustments zero."""
    seed = np.zeros(5, dtype=np.float64)
    edges = [(0, 1, 0.5, "SUPPLY"), (1, 2, 0.4, "CUSTOMER")]
    
    hops, final_total, reconciliation, _ = propagate_kernel(seed, edges, max_hops=4)
    
    assert np.allclose(hops, 0.0)
    assert np.allclose(final_total, 0.0)
    assert np.allclose(reconciliation, 0.0)


def test_n04_decay_chain():
    """N-04: A->B->C; weights .4 / .5; alpha .65; seed .10.
    B=.026 at hop1; C=.00845 at hop2; analytical unclipped fixture.
    """
    # Node 0 (A), Node 1 (B), Node 2 (C)
    seed = np.array([0.10, 0.0, 0.0], dtype=np.float64)
    edges = [
        (0, 1, 0.4, "GENERIC"),  # A -> B, weight 0.4
        (1, 2, 0.5, "GENERIC"),  # B -> C, weight 0.5
    ]
    
    hops, final_total, reconciliation, _ = propagate_kernel(seed, edges, alpha=0.65, max_hops=4)
    
    # Hop 0: A = 0.10, B = 0, C = 0
    assert np.isclose(hops[0, 0], 0.10)
    assert np.isclose(hops[0, 1], 0.0)
    assert np.isclose(hops[0, 2], 0.0)

    # Hop 1: B = alpha * 0.4 * 0.10 = 0.65 * 0.4 * 0.10 = 0.026
    assert np.isclose(hops[1, 1], 0.026, atol=1e-7), f"B at hop1 expected 0.026, got {hops[1, 1]}"
    assert np.isclose(hops[1, 2], 0.0)

    # Hop 2: C = alpha * 0.5 * B_hop1 = 0.65 * 0.5 * 0.026 = 0.00845
    assert np.isclose(hops[2, 2], 0.00845, atol=1e-7), f"C at hop2 expected 0.00845, got {hops[2, 2]}"

    # Hop 3 & 4 should be 0.0
    assert np.isclose(hops[3, 2], 0.0)
    assert np.isclose(hops[4, 2], 0.0)


def test_n05_branch_join():
    """N-05: One source splits then joins. Independent channel totals match exact sum."""
    # Node 0 (A) -> Node 1 (B) [weight 0.4], Node 0 (A) -> Node 2 (C) [weight 0.6]
    # Both B and C -> Node 3 (D) [weights 0.5 each]
    seed = np.array([0.10, 0.0, 0.0, 0.0], dtype=np.float64)
    edges = [
        (0, 1, 0.4, "GENERIC"),
        (0, 2, 0.6, "GENERIC"),
        (1, 3, 0.5, "GENERIC"),
        (2, 3, 0.5, "GENERIC"),
    ]
    
    hops, final_total, _, _ = propagate_kernel(seed, edges, alpha=0.65, max_hops=4)
    
    # Hop 1:
    # B = 0.65 * 0.4 * 0.10 = 0.026
    # C = 0.65 * 0.6 * 0.10 = 0.039
    assert np.isclose(hops[1, 1], 0.026)
    assert np.isclose(hops[1, 2], 0.039)

    # Hop 2:
    # D from B = 0.65 * 0.5 * 0.026 = 0.00845
    # D from C = 0.65 * 0.5 * 0.039 = 0.012675
    # Total D at hop 2 = 0.00845 + 0.012675 = 0.021125
    expected_d_hop2 = 0.65 * 0.5 * (0.026 + 0.039)
    assert np.isclose(hops[2, 3], expected_d_hop2)


def test_n06_distress():
    """N-06: Equal positive / negative channel inputs.
    Only negative channel amplified; missing-data policy visible.
    """
    # Node 0 (+0.10), Node 1 (-0.10)
    # Both feed into Node 2 with weight 0.5
    # Distress multiplier for Node 2 is 1.40
    seed_pos = np.array([0.10, 0.0, 0.0], dtype=np.float64)
    seed_neg = np.array([0.0, -0.10, 0.0], dtype=np.float64)
    edges = [(0, 2, 0.5, "GENERIC"), (1, 2, 0.5, "GENERIC")]
    distress = np.array([1.0, 1.0, 1.40], dtype=np.float64)
    
    hops_pos, _, _, _ = propagate_kernel(seed_pos, edges, distress=distress, alpha=0.65)
    hops_neg, _, _, _ = propagate_kernel(seed_neg, edges, distress=distress, alpha=0.65)
    
    # Positive impulse: unamplified = 0.65 * 0.5 * 0.10 = 0.0325
    assert np.isclose(hops_pos[1, 2], 0.0325)
    
    # Negative impulse: amplified by 1.40 = 0.65 * 0.5 * (-0.10) * 1.40 = -0.0455
    assert np.isclose(hops_neg[1, 2], -0.0455)
    assert abs(hops_neg[1, 2]) > hops_pos[1, 2] * 1.39


def test_n07_substitution():
    """N-07: Supply + rate incoming edges. Only supply uses (1 - substitution)."""
    # Node 0 (Supply source) -> Node 2, weight 0.5, relation="SUPPLY"
    # Node 1 (Credit source) -> Node 2, weight 0.5, relation="CREDIT"
    # Target Node 2 has substitution = 0.30
    seed_supply = np.array([0.10, 0.0, 0.0], dtype=np.float64)
    seed_credit = np.array([0.0, 0.10, 0.0], dtype=np.float64)
    edges = [
        (0, 2, 0.5, "SUPPLY"),
        (1, 2, 0.5, "CREDIT"),
    ]
    substitution = np.array([0.0, 0.0, 0.30], dtype=np.float64)
    
    hops_sup, _, _, _ = propagate_kernel(seed_supply, edges, substitution=substitution, alpha=0.65)
    hops_crd, _, _, _ = propagate_kernel(seed_credit, edges, substitution=substitution, alpha=0.65)
    
    # Supply channel discounted by (1 - 0.30) = 0.70: 0.65 * 0.5 * 0.10 * 0.70 = 0.02275
    assert np.isclose(hops_sup[1, 2], 0.02275)
    # Credit channel NOT discounted: 0.65 * 0.5 * 0.10 = 0.0325
    assert np.isclose(hops_crd[1, 2], 0.0325)


def test_n08_cycles():
    """N-08: A<->B; bounded weights. Exactly K rounds; repeated-node diagnostics; no infinite traversal."""
    # Mutual cycle: 0 -> 1 (0.8) and 1 -> 0 (0.8)
    seed = np.array([0.20, 0.0], dtype=np.float64)
    edges = [
        (0, 1, 0.8, "GENERIC"),
        (1, 0, 0.8, "GENERIC"),
    ]
    
    hops, final_total, _, diagnostics = propagate_kernel(seed, edges, alpha=0.65, max_hops=4)
    
    assert hops.shape == (5, 2)
    assert len(diagnostics) == 4
    # Check that impulses decay geometrically: decay rate = alpha * weight = 0.65 * 0.8 = 0.52
    assert abs(hops[2, 0]) < abs(hops[0, 0])
    assert abs(hops[4, 0]) < abs(hops[2, 0])


def test_n09_clipping():
    """N-09: Raw summed return beyond bounds. Aggregate first; explicit adjustment reconciles final."""
    # Massive negative shock exceeding -0.95 bound
    seed = np.array([-0.80, 0.0], dtype=np.float64)
    edges = [(0, 1, 1.0, "GENERIC")]
    distress = np.array([1.0, 2.5], dtype=np.float64)
    
    hops, final_total, reconciliation, _ = propagate_kernel(
        seed, edges, distress=distress, alpha=0.65, clip_min=-0.95, clip_max=2.00
    )
    
    # Raw sum is sum(hops)
    raw_sum_tgt = np.sum(hops[:, 1])
    # Target hop 1 is 0.65 * 1.0 * (-0.80) * 2.5 = -1.30
    assert raw_sum_tgt < -0.95
    assert final_total[1] == -0.95
    # Explicit reconciliation adjustment: final - raw > 0
    assert np.isclose(reconciliation[1], final_total[1] - raw_sum_tgt)


def test_n10_fx():
    """N-10: Known local / FX returns. Compounded base return includes cross-term:
    (1 + r_local)*(1 + r_fx) - 1.
    """
    r_local = -0.10
    r_fx = -0.05
    r_base = compound_return(r_local, r_fx)
    
    # Analytical: (1 - 0.10)*(1 - 0.05) - 1 = 0.90 * 0.95 - 1 = 0.855 - 1 = -0.145
    expected = -0.145
    assert np.isclose(r_base, expected), f"Expected {expected}, got {r_base}"
    
    # Verify cross-term difference from simple addition (-0.15)
    simple_add = r_local + r_fx
    assert not np.isclose(r_base, simple_add)
    assert np.isclose(r_base, simple_add + r_local * r_fx)


def test_n11_ratio_invalid():
    """N-11: Negative EBITDA / absent coverage. Named policy / warning, no NaN / healthy silent fill."""
    from app.engine.propagator import ContagionPropagator
    import pandas as pd
    
    prop = ContagionPropagator()
    # Node with negative EBITDA (invalid leverage ratio)
    nodes_df = pd.DataFrame([
        {"node_id": "DISTRESSED_CO", "node_type": "ASSET", "net_debt_ebitda": -5.0, "int_coverage": -0.5},
        {"node_id": "HEALTHY_CO", "node_type": "ASSET", "net_debt_ebitda": 1.2, "int_coverage": 6.0},
    ])
    
    lambdas = prop.compute_distress_multipliers(nodes_df)
    # Must be finite, not NaN
    assert np.all(np.isfinite(lambdas))
    # Negative interest coverage indicates distress (int_coverage < 1.5)
    assert lambdas[0] >= 1.0


def test_n12_units():
    """N-12: Rate bps vs return fraction mismatch. Reject before propagation; no guessed conversion."""
    # BPS factor given fraction unit must raise INPUT_UNIT_MISMATCH
    with pytest.raises(ContagionDomainException) as exc_info:
        validate_factor_shock(factor_id="US10Y_REAL", unit="fraction", value=200.0)
    assert exc_info.value.code == FailureCode.INPUT_UNIT_MISMATCH

    # Valid bps unit succeeds
    norm_val = validate_factor_shock(factor_id="US10Y_REAL", unit="bps", value=200.0)
    assert np.isclose(norm_val, 0.02)
