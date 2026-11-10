"""Minsky Time-Series Output Normalizer per Section 21.4.
Normalizes adaptive solver outputs to a declared simulation time-grid,
converts level series to changes against baselines, and produces schema-valid FactorShock models.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from app.domain.errors import ContagionDomainException, FailureCode
from app.domain.factor_registry import FACTOR_REGISTRY, validate_factor_shock
from app.domain.models import FactorShock, ShockPoint


DEFAULT_VARIABLE_MAP = {
    "spread": ("SOFR_SPREAD", "bps", 10000.0),  # fraction to bps
    "hy_spread": ("HY_OAS", "bps", 10000.0),
    "oil": ("BRENT_CRUDE", "price_fraction", 1.0),
    "capacity": ("FOUNDRY_TW", "fraction", 1.0),
}


def normalize_minsky_output(
    df: pd.DataFrame,
    variable_mapping: Optional[Dict[str, tuple]] = None,
    grid_points: int = 20,
) -> List[FactorShock]:
    """Normalizes raw Minsky simulation dataframe to FactorShock instances.
    
    Args:
        df: DataFrame with 'time' column and one or more variable columns.
        variable_mapping: Dict mapping column -> (factor_id, canonical_unit, scale_factor)
        grid_points: Target uniform time-grid points (default 20 days)
    """
    if "time" not in df.columns:
        raise ContagionDomainException(
            code=FailureCode.MINSKY_OUTPUT_INVALID,
            message="Minsky output missing required 'time' column",
        )

    var_map = variable_mapping or DEFAULT_VARIABLE_MAP
    shocks: List[FactorShock] = []
    
    # Sort by time
    df_sorted = df.sort_values("time").dropna()
    times = df_sorted["time"].to_numpy()
    if len(times) < 2:
        raise ContagionDomainException(
            code=FailureCode.MINSKY_OUTPUT_INVALID,
            message="Minsky output has insufficient time steps",
        )

    # Uniform grid
    t_uniform = np.linspace(times[0], times[-1], grid_points)

    for col, (factor_id, unit, scale) in var_map.items():
        if col not in df_sorted.columns:
            continue

        raw_values = df_sorted[col].to_numpy()
        if not np.all(np.isfinite(raw_values)):
            raise ContagionDomainException(
                code=FailureCode.MINSKY_OUTPUT_INVALID,
                message=f"Non-finite values found in Minsky column '{col}'",
            )

        # Baseline: value at t=0
        baseline_val = raw_values[0]
        # Incremental changes or level deltas
        delta_vals = (raw_values - baseline_val) * scale
        
        # Interpolate onto uniform time grid
        interp_vals = np.interp(t_uniform, times, delta_vals)
        
        points = tuple(
            ShockPoint(t=float(round(t_uniform[i], 3)), value=float(round(interp_vals[i], 4)))
            for i in range(grid_points)
        )
        
        # Validate unit and range against FACTOR_REGISTRY
        for pt in points:
            validate_factor_shock(factor_id, unit, pt.value)

        shocks.append(
            FactorShock(
                factor_id=factor_id,
                unit=unit,
                kind="level_path",
                baseline_id="MINSKY_RUN",
                horizon_days=grid_points,
                points=points,
            )
        )

    return shocks
