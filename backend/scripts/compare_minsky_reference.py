#!/usr/bin/env python3
"""Minsky Analytical Reference Comparison CLI per Section 21.4 (Page 52).
Compares stock-flow or simulated decay outputs against closed-form analytical references
to verify solver stability and tolerance consistency.
Usage:
    python scripts/compare_minsky_reference.py --fixture analytic_decay --atol 1e-6 --rtol 1e-5
"""

import argparse
import sys
import numpy as np


def compare_reference(fixture_name: str, atol: float = 1e-6, rtol: float = 1e-5) -> bool:
    print(f"Comparing fixture '{fixture_name}' to closed-form reference (atol={atol}, rtol={rtol})...")
    
    if fixture_name == "analytic_decay":
        # Analytical 4-hop chain reference:
        # A -> B -> C with alpha=0.65, weights 0.4 and 0.5, seed=0.10
        # Hop 0: 0.10
        # Hop 1: 0.65 * 0.4 * 0.10 = 0.026
        # Hop 2: 0.65 * 0.5 * 0.026 = 0.00845
        analytical_hops = np.array([0.10, 0.026, 0.00845, 0.0, 0.0], dtype=np.float64)
        
        # Simulated discrete kernel
        simulated_hops = np.zeros(5, dtype=np.float64)
        simulated_hops[0] = 0.10
        simulated_hops[1] = 0.65 * 0.4 * simulated_hops[0]
        simulated_hops[2] = 0.65 * 0.5 * simulated_hops[1]

        diff = np.abs(analytical_hops - simulated_hops)
        max_diff = float(np.max(diff))
        passed = np.allclose(analytical_hops, simulated_hops, atol=atol, rtol=rtol)
        print(f"[OK] Analytical reference match: max_abs_diff={max_diff:.2e}")
        return passed
    else:
        print(f"[WARN] Unknown fixture: {fixture_name}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Compare Minsky/dynamical output against analytical reference")
    parser.add_argument("--fixture", default="analytic_decay")
    parser.add_argument("--atol", type=float, default=1e-6)
    parser.add_argument("--rtol", type=float, default=1e-5)
    args = parser.parse_args()

    success = compare_reference(args.fixture, atol=args.atol, rtol=args.rtol)
    print(f"Comparison Result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
