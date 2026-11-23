#!/usr/bin/env python3
"""
RiskLattice Automated Chaos Engineering & Resilience Drill.
Executes an adversarial testing battery against pure quant engines:
- Cyclic graph feedback loop damping
- Singular / collinear covariance PSD repair (Higham 2002)
- Extreme leverage balance sheet cliffs (D/E up to 10^6)
- Degenerate inventory buffer bounds (negative / infinite days)
- Disconnected network components & orphan nodes
- Malformed shock vectors (NaN, Inf, out-of-bounds)
- Gateway Circuit Breaker state transitions & fail-open verification

Usage:
    .venv/bin/python backend/scripts/chaos_drill.py
"""

import sys
import time
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.engine.chaos import run_comprehensive_chaos_suite
from app.services.circuit_breaker_service import CircuitBreakerService, CircuitState


def main():
    print("=" * 72)
    print("   RISKLATTICE AUTOMATED CHAOS ENGINEERING & RESILIENCE DRILL   ")
    print("=" * 72)
    print("Executing adversarial quantitative battery & circuit breaker tests...\n")

    t_start = time.time()

    # 1. Run Mathematical Engine Chaos Suite
    reports = run_comprehensive_chaos_suite()

    # 2. Run Gateway Circuit Breaker Verification
    cb = CircuitBreakerService(name="cli_chaos_breaker", failure_threshold=2, recovery_timeout=0.05)
    cb.trip("Simulated network black swan")
    tripped_ok = cb.state == CircuitState.OPEN
    fallback_ok = cb.call(lambda: 1 / 0, fallback=lambda: "FALLBACK_VERIFIED") == "FALLBACK_VERIFIED"
    time.sleep(0.06)
    half_open_ok = cb.state == CircuitState.HALF_OPEN
    cb.record_success()
    cb.record_success()
    reset_ok = cb.state == CircuitState.CLOSED

    cb_drill_passed = tripped_ok and fallback_ok and half_open_ok and reset_ok

    total_duration = time.time() - t_start

    # Format Output Table
    print(f"{'DRILL NAME':<40} | {'STATUS':<8} | {'TIME (ms)':<10} | {'NOTES'}")
    print("-" * 72)

    all_passed = True
    for r in reports:
        status_str = "PASS" if r.passed else "FAIL"
        if not r.passed:
            all_passed = False
        print(f"{r.test_name:<40} | {status_str:<8} | {r.execution_time_ms:>8.2f}ms | {r.stability_notes}")

    cb_status_str = "PASS" if cb_drill_passed else "FAIL"
    if not cb_drill_passed:
        all_passed = False
    print(f"{'Gateway Circuit Breaker State Machine':<40} | {cb_status_str:<8} | {total_duration * 1000:>8.2f}ms | Closed->Open->HalfOpen->Closed verified")

    print("-" * 72)
    total_drills = len(reports) + 1
    passed_count = sum(1 for r in reports if r.passed) + (1 if cb_drill_passed else 0)

    print(f"\nRESULTS: {passed_count}/{total_drills} Drills Passed in {total_duration:.3f}s")

    if all_passed:
        print("\n[SUCCESS] All quantitative engines and gateway resilient to adversarial chaos.")
        sys.exit(0)
    else:
        print("\n[FAILURE] One or more chaos drills failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
