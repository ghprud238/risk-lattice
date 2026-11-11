#!/usr/bin/env python3
"""System Diagnostic & Health Check per Section 20.4 & 21.1.
Verifies Python version, memory, port availability, fixture integrity, and optional Minsky capabilities.
Usage:
    python scripts/doctor.py [--profile minsky-local] [--minsky-python /path/to/python]
"""

import argparse
import os
import socket
import sys

# Ensure backend root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integrations.minsky.probe import probe_minsky


def check_port_free(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        res = s.connect_ex((host, port))
        return res != 0  # True if port is free (connection failed)


def main():
    parser = argparse.ArgumentParser(description="ContagionGraph System Doctor")
    parser.add_argument("--profile", default="core", choices=["core", "minsky-local"])
    parser.add_argument("--minsky-python", default=None)
    parser.add_argument("--check-model-manifest", action="store_true")
    parser.add_argument("--model", default="fixtures/minsky/liquidity_freeze.mky")
    args = parser.parse_args()

    print("=" * 60)
    print("ContagionGraph Diagnostic Health Check (doctor.py)")
    print("=" * 60)

    # 1. Python version check
    py_ver = sys.version_info
    py_ok = (py_ver.major == 3 and py_ver.minor >= 11)
    status_py = "PASS" if py_ok else "FAIL"
    print(f"[{status_py}] Python Version: {sys.version.split()[0]} (>= 3.11 required)")

    # 2. Database & Data directory check
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
    db_path = os.path.join(data_dir, "contagion.duckdb")
    db_ok = os.path.exists(db_path)
    status_db = "PASS" if db_ok else "WARN"
    print(f"[{status_db}] Catalog Database: {db_path} ({'Found' if db_ok else 'Not seeded yet. Run make seed'})")

    # 3. Filings Corpus check
    filings_path = os.path.join(data_dir, "synthetic/filings_corpus.json")
    filings_ok = os.path.exists(filings_path)
    status_filings = "PASS" if filings_ok else "WARN"
    print(f"[{status_filings}] SEC Filings Corpus: {filings_path} ({'Found' if filings_ok else 'Missing'})")

    # 4. Port availability check (5051 backend, 5050 frontend)
    p5051_free = check_port_free(5051)
    p5050_free = check_port_free(5050)
    print(f"[{'PASS' if p5051_free else 'WARN'}] Port 5051 (Backend API): {'Free' if p5051_free else 'In use / occupied'}")
    print(f"[{'PASS' if p5050_free else 'WARN'}] Port 5050 (Frontend Web): {'Free' if p5050_free else 'In use / occupied'}")

    # 5. Core dependencies check
    deps = ["numpy", "scipy", "duckdb", "pandas", "fastapi", "litellm", "pydantic"]
    missing = []
    for d in deps:
        try:
            __import__(d)
        except ImportError:
            missing.append(d)
    status_deps = "PASS" if not missing else "FAIL"
    print(f"[{status_deps}] Core Math & Web Packages: {'All installed' if not missing else 'Missing: ' + ', '.join(missing)}")

    # 6. Minsky Profile Check (Optional capability per Section 21.1)
    if args.profile == "minsky-local" or os.getenv("MINSKY_ENABLED", "").lower() == "true":
        print("-" * 60)
        print("Optional Minsky Capability Check:")
        probe = probe_minsky(args.minsky_python)
        status_minsky = "PASS" if probe.available else "SKIP"
        print(f"[{status_minsky}] pyminsky Status: {probe.message}")
        if args.check_model_manifest and os.path.exists(args.model):
            print(f"[PASS] Model Fixture: {args.model} found")
    else:
        print("[INFO] Minsky Simulator: Skipped (profile='core', optional capability)")

    print("=" * 60)
    overall_ok = py_ok and not missing
    print(f"Overall System Status: {'READY' if overall_ok else 'ATTENTION REQUIRED'}")
    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
