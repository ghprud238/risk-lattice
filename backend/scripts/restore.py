#!/usr/bin/env python3
"""Point-in-Time Catalog & Artifact Restore Script per Section 26.1.
Restores catalog.duckdb and artifacts from a specified tar.gz backup archive.
Usage:
    python scripts/restore.py <backup_archive.tar.gz> [--target-dir data]
"""

import argparse
import os
import sys
import tarfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def restore_backup(archive_path: str, target_dir: str):
    if not os.path.exists(archive_path):
        print(f"[FAIL] Backup archive not found: {archive_path}")
        sys.exit(1)

    print(f"Restoring backup from: {archive_path} into {target_dir}")
    os.makedirs(target_dir, exist_ok=True)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=target_dir)

    print("[SUCCESS] Restore completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore catalog and artifacts from backup")
    parser.add_argument("archive", help="Path to backup tar.gz archive")
    parser.add_argument("--target-dir", default=os.path.join(os.path.dirname(__file__), "../data"))
    args = parser.parse_args()
    restore_backup(args.archive, args.target_dir)
