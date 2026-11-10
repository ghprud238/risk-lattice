#!/usr/bin/env python3
"""Minsky Output Normalization CLI per Section 21.4.
Normalizes adaptive solver outputs to a uniform time-grid and exports schema-valid Scenario JSON.
Usage:
    python scripts/normalize_minsky.py --input <csv> --manifest <manifest.json> --output <out.json>
"""

import argparse
import json
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integrations.minsky.normalizer import normalize_minsky_output


def main():
    parser = argparse.ArgumentParser(description="Normalize Minsky CSV to Scenario Draft JSON")
    parser.add_argument("--input", required=True, help="Input raw Minsky CSV")
    parser.add_argument("--manifest", required=True, help="Path to model manifest JSON")
    parser.add_argument("--output", required=True, help="Output Scenario JSON file path")
    parser.add_argument("--grid-points", type=int, default=20)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[FAIL] Input file not found: {args.input}")
        sys.exit(1)

    df = pd.read_csv(args.input)
    with open(args.manifest, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Build var mapping from manifest
    var_map = {}
    for col, spec in manifest.get("variables", {}).items():
        var_map[col] = (spec["factor_id"], spec["unit"], spec.get("canonical_scale", 1.0))

    shocks = normalize_minsky_output(df, variable_mapping=var_map, grid_points=args.grid_points)
    
    payload = {
        "schema_version": "1",
        "scenario_name": manifest.get("name", "Normalized Minsky Scenario"),
        "shocks": [
            {
                "factor_id": s.factor_id,
                "unit": s.unit,
                "kind": s.kind,
                "baseline_id": s.baseline_id,
                "horizon_days": s.horizon_days,
                "points": [{"t": p.t, "value": p.value} for p in s.points],
            }
            for s in shocks
        ],
        "assumptions": [f"Derived from Minsky model {manifest.get('model_id', 'unknown')}"],
        "unresolved": [],
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"[SUCCESS] Normalized {len(shocks)} factor shocks written to: {args.output}")


if __name__ == "__main__":
    main()
