#!/usr/bin/env python3
"""Database & Storage Layout Initializer per Section 14.2 & 20.1.
Creates the local directory layout:
  data/private/catalog.duckdb
  data/private/artifacts/
  data/tmp/attempts/
"""

import os
import sys

# Ensure backend root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import db_manager


def init_storage():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dirs = [
        os.path.join(base_dir, "data/private"),
        os.path.join(base_dir, "data/private/artifacts"),
        os.path.join(base_dir, "data/tmp/attempts"),
        os.path.join(base_dir, "data/backups"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"[OK] Directory verified: {d}")

    # Initialize DuckDB schema
    db_manager.initialize_schema()
    print("[OK] DuckDB schema initialized successfully.")


if __name__ == "__main__":
    init_storage()
