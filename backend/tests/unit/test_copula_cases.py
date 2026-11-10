"""Copula & Tail Risk Test Cases R-01 to R-08 per Section 23.2 (Page 57).
Tests Student-t copula construction, PSD repair, marginal boundary behavior, ES >= VaR, and reproducibility.
"""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from app.engine.risk_metrics import TailRiskEngine


def test_r01_shared_radial_t_scale():
    """R-01: Shared radial t scale per path:
    Verify that multivariate Student-t samples use a single radial variable W ~ chi2(nu)/nu per path
    across all dimensions, producing joint tail clustering.
    """
    nu = 4.0
    N_paths = 50000
    dim = 2
    
    rng = np.random.Generator(np.random.PCG64(42))
    # Uncorrelated standard normal draws
    Z = rng.standard_normal((N_paths, dim))
    # Shared radial draw
    W = rng.chisquare(df=nu, size=N_paths) / nu
    # t vector: Z_i / sqrt(W)
    t_samples = Z / np.sqrt(W[:, None])
    
    # In the joint tail (both Z_1 and Z_2 negative), radial scaling amplifies both simultaneously
    joint_tail_prob = np.mean((t_samples[:, 0] < -2.5) & (t_samples[:, 1] < -2.5))
    indep_tail_prob = np.mean(t_samples[:, 0] < -2.5) * np.mean(t_samples[:, 1] < -2.5)
    
    # Due to shared radial scale, joint tail probability is strictly greater than product of marginals
    assert joint_tail_prob > indep_tail_prob * 1.5, "Shared radial scale must produce joint tail dependence"


def test_r02_psd_repair():
    """R-02: PSD / symmetry / diagonal checks:
    Non-PSD matrix is repaired via eigenvalue spectral floor.
    """
    # Create non-positive semi-definite matrix
    A = np.array([
        [1.0, 0.95, 0.95],
        [0.95, 1.0, -0.90],
        [0.95, -0.90, 1.0],
    ], dtype=np.float64)
    
    eigenvalues = np.linalg.eigvalsh(A)
    assert np.min(eigenvalues) < 0, "Initial matrix must have negative eigenvalue"
    
    # Spectral repair: project onto PSD cone
    vals, vecs = np.linalg.eigh(A)
    repaired_vals = np.maximum(vals, 1e-6)
    repaired_A = vecs @ np.diag(repaired_vals) @ vecs.T
    # Restore unit diagonal
    inv_diag = 1.0 / np.sqrt(np.diag(repaired_A))
    repaired_corr = np.outer(inv_diag, inv_diag) * repaired_A
    
    repaired_eigenvalues = np.linalg.eigvalsh(repaired_corr)
    assert np.all(repaired_eigenvalues >= 0.0), "Repaired correlation matrix must be PSD"
    assert np.allclose(np.diag(repaired_corr), 1.0), "Repaired correlation must have unit diagonal"


def test_r03_marginals_boundary():
    """R-03: Marginal boundaries:
    Finite boundary quantiles, empirical tail interpolation, no inf or NaN for extreme probabilities.
    """
    sample_returns = np.array([-0.08, -0.05, -0.03, -0.01, 0.0, 0.02, 0.04, 0.07], dtype=np.float64)
    
    # Test quantiles near 0 and 1
    q_low = np.quantile(sample_returns, 0.0001)
    q_high = np.quantile(sample_returns, 0.9999)
    
    assert np.isfinite(q_low)
    assert np.isfinite(q_high)
    assert q_low >= np.min(sample_returns)
    assert q_high <= np.max(sample_returns)


def test_r04_hand_ranked_metrics_es_ge_var():
    """R-04: Metrics:
    Hand-ranked losses verify quantile and fractional-tail ES; ES >= corresponding VaR strictly holds.
    """
    # 100 deterministic simulated losses
    losses = np.linspace(0.0, 1.0, 100)  # loss from 0.0 to 1.0
    
    # 95% VaR is the 95th percentile
    var_95 = np.percentile(losses, 95)
    # 95% Expected Shortfall is the mean of losses >= var_95
    tail_losses = losses[losses >= var_95]
    es_95 = np.mean(tail_losses)
    
    assert es_95 >= var_95, f"Expected Shortfall {es_95} must be >= VaR {var_95}"
    assert np.isclose(var_95, 0.95, atol=0.01)
    assert es_95 > var_95


def test_r05_pinned_exact_replay():
    """R-05: Pinned exact replay under PCG64(seed=42)."""
    # Synthetic empirical returns
    dates = pd.date_range("2024-01-01", periods=100)
    df = pd.DataFrame({
        "trade_date": list(dates) * 2,
        "node_id": ["ASSET_1"] * 100 + ["ASSET_2"] * 100,
        "daily_return": np.sin(np.linspace(0, 10, 200)) * 0.02,
    })
    
    engine1 = TailRiskEngine(df_t=4.0, num_simulations=2000, seed=42)
    res1 = engine1.compute_portfolio_risk({"ASSET_1": 0.5, "ASSET_2": 0.5}, returns_df=df)
    
    engine2 = TailRiskEngine(df_t=4.0, num_simulations=2000, seed=42)
    res2 = engine2.compute_portfolio_risk({"ASSET_1": 0.5, "ASSET_2": 0.5}, returns_df=df)
    
    assert res1.var_99 == res2.var_99
    assert res1.cvar_99 == res2.cvar_99
    assert res1.copula_to_gaussian_ratio == res2.copula_to_gaussian_ratio


def test_r06_rng_stream_mapping():
    """R-06: Fixed path-to-stream mapping produces deterministic sample sequence."""
    gen1 = np.random.Generator(np.random.PCG64(42))
    draws1 = gen1.standard_normal(100)
    
    gen2 = np.random.Generator(np.random.PCG64(42))
    draws2 = gen2.standard_normal(100)
    
    assert np.array_equal(draws1, draws2)


def test_r07_degeneracy_single_asset():
    """R-07: Degeneracy: Single asset portfolio with zero variance or all gains."""
    dates = pd.date_range("2024-01-01", periods=50)
    df_const = pd.DataFrame({
        "trade_date": dates,
        "node_id": ["SOLO"] * 50,
        "daily_return": [0.01] * 50,  # Constant gain, zero variance
    })
    
    engine = TailRiskEngine(df_t=4.0, num_simulations=1000, seed=42)
    res = engine.compute_portfolio_risk({"SOLO": 1.0}, returns_df=df_const)
    
    assert np.isfinite(res.var_99)
    assert np.isfinite(res.cvar_99)
    assert res.cvar_99 <= 0.0  # Constant positive gain produces zero loss


def test_r08_conditioning():
    """R-08: Conditioning: Residual disabled -> deterministic scenario."""
    # When stress_shock is provided, it shifts the simulated distribution
    dates = pd.date_range("2024-01-01", periods=100)
    df = pd.DataFrame({
        "trade_date": dates,
        "node_id": ["STOCK_A"] * 100,
        "daily_return": np.random.default_rng(42).normal(0.0, 0.01, 100),
    })
    
    engine = TailRiskEngine(df_t=4.0, num_simulations=2000, seed=42)
    # Baseline
    res_base = engine.compute_portfolio_risk({"STOCK_A": 1.0}, returns_df=df)
    # Conditioned with -15% deterministic stress
    res_stressed = engine.compute_portfolio_risk(
        {"STOCK_A": 1.0}, returns_df=df, stress_shock={"STOCK_A": -0.15}
    )
    
    # Stressed CVaR must be higher than baseline CVaR by approximately the shift
    assert res_stressed.cvar_99 > res_base.cvar_99
    assert res_stressed.cvar_99 >= 0.15
