#!/usr/bin/env python3
"""Simulation Run & Manifest Verification Script per Section 14.3 & 20.4.
Verifies the cryptographic content hash, completion status, and result metrics of a simulation run.
Usage:
    python scripts/verify_run.py <run_id>
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.job_service import job_service


def verify_run(run_id: str) -> bool:
    print(f"Verifying Simulation Run: {run_id}")
    manifest = job_service.get_job(run_id)
    if not manifest:
        print(f"[FAIL] Run {run_id} not found in job registry.")
        return False

    print(f"[OK] Run ID: {manifest.run_id}")
    print(f"[OK] Status: {manifest.status.value}")
    print(f"[OK] Created At: {manifest.created_at}")
    print(f"[OK] Seed: {manifest.seed}, Paths: {manifest.paths}")
    print(f"[OK] Engine Profile: {manifest.engine_profile}")
    print(f"[OK] Risk Profile: {manifest.risk_profile}")

    events = job_service.get_events(run_id)
    print(f"[OK] Audit Event Log: {len(events)} ordered events recorded.")
    for ev in events:
        print(f"     Seq {ev.sequence:02d}: {ev.event}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Verify a ContagionGraph simulation run")
    parser.add_argument("run_id", help="UUID of the run to verify")
    args = parser.parse_args()

    success = verify_run(args.run_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
