#!/usr/bin/env python3
"""
Alias runner for seed_data.py per PRD Section 6.1
"""
import sys
from pathlib import Path

# Add scripts directory to path and execute main
scripts_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(scripts_dir))

from seed_data import seed_database, parser

if __name__ == "__main__":
    args = parser.parse_args()
    seed_database(verify=args.verify)
