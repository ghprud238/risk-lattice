#!/usr/bin/env python3
"""Point-in-Time Catalog & Artifact Backup Script per Section 26.1.
Creates a timestamped compressed archive of catalog.duckdb and immutable artifacts.
Usage:
    python scripts/backup.py [--out-dir data/backups]
"""

import argparse
from datetime import datetime, timezone
import os
import shutil
import sys
import tarfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def create_backup(out_dir: str) -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(out_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(out_dir, f"contagion_backup_{timestamp}.tar.gz")

    print(f"Creating backup archive: {backup_file}")
    with tarfile.open(backup_file, "w:gz") as tar:
        # Include catalog db
        db_path = os.path.join(data_dir, "contagion.duckdb")
        if os.path.exists(db_path):
            tar.add(db_path, arcname="contagion.duckdb")
            print("  [+] Added catalog database")

        # Include private artifacts
        artifacts_dir = os.path.join(data_dir, "private")
        if os.path.exists(artifacts_dir):
            tar.add(artifacts_dir, arcname="private")
            print("  [+] Added private artifacts directory")

    size_mb = os.path.getsize(backup_file) / (1024 * 1024)
    print(f"[SUCCESS] Backup completed: {backup_file} ({size_mb:.2f} MB)")
    return backup_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup catalog database and artifacts")
    parser.add_argument("--out-dir", default=os.path.join(os.path.dirname(__file__), "../data/backups"))
    args = parser.parse_args()
    create_backup(args.out_dir)
