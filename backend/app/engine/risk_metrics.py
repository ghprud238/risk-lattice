"""
Tail-Risk & Student-t Copula Monte Carlo Engine.
PRD Section 4, 5 & 6:
- 10,000-path Student-t copula simulations (nu = 4, seed = 42)
- PCG64(42) pseudo-random number generator for bit-exact reproducibility
- 95% / 99% VaR and CVaR (Expected Shortfall)
- Baseline 60-day Gaussian VaR benchmark
- Marginal risk decomposition
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy import stats

from app.db.database import db_manager


class RiskMetricsResult(BaseModel):
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    gaussian_var_99: float
    copula_to_gaussian_ratio: float
    num_simulations: int
    asset_marginal_risks: Dict[str, float]


class TailRiskEngine:
    def __init__(self, df_t: float = 4.0, num_simulations: int = 10000, seed: int = 42):
        self.df_t = df_t
        self.num_simulations = num_simulations
        self.seed = seed

    def compute_portfolio_risk(
        self,
        portfolio_weights: Dict[str, float],
        returns_df: Optional[pd.DataFrame] = None,
        stress_shock: Optional[Dict[str, float]] = None
    ) -> RiskMetricsResult:
        """
        Runs 10,000 Student-t copula simulations with nu=4.0 and PCG64(42) PRNG.
        Computes 95%/99% VaR, CVaR, and Gaussian VaR.
        """
        # Strictly seed the generator with PCG64(42)
        rng = np.random.Generator(np.random.PCG64(self.seed))

        holdings = list(portfolio_weights.keys())
        weights = np.array([portfolio_weights[h] for h in holdings], dtype=np.float64)
        if np.sum(np.abs(weights)) == 0:
            weights = np.ones(len(holdings)) / max(1, len(holdings))
        else:
            weights = weights / np.sum(weights)

        # Retrieve empirical returns for holdings
        if returns_df is None:
            placeholders = ", ".join(f"'{h}'" for h in holdings)
            query = f"""
                SELECT trade_date, node_id, daily_return
                FROM macro_returns
                WHERE node_id IN ({placeholders})
                ORDER BY trade_date, node_id;
            """
            returns_df = db_manager.query_df(query)

        pivoted = returns_df.pivot(index="trade_date", columns="node_id", values="daily_return").dropna()
        # Ensure ordering aligns with holdings
        available_holdings = [h for h in holdings if h in pivoted.columns]
        if not available_holdings:
            # Fallback for empty/unmatched
            return RiskMetricsResult(
                var_95=0.0,
                var_99=0.0,
                cvar_95=0.0,
                cvar_99=0.0,
                gaussian_var_99=0.0,
                copula_to_gaussian_ratio=1.0,
                num_simulations=self.num_simulations,
                asset_marginal_risks={h: 0.0 for h in holdings}
            )

        avail_weights = np.array([portfolio_weights[h] for h in available_holdings], dtype=np.float64)
        avail_weights = avail_weights / np.sum(avail_weights)

        R = pivoted[available_holdings].values # shape (T, K)
        T, K = R.shape

        # Calculate sample covariance and correlation matrix
        cov_matrix = np.cov(R, rowvar=False)
        std_devs = np.std(R, axis=0) + 1e-8
        corr_matrix = np.corrcoef(R, rowvar=False)

        # Cholesky decomposition of correlation matrix for Student-t copula
        # Add small regularizer to guarantee positive definiteness
        reg_corr = corr_matrix + np.eye(K) * 1e-7
        L = np.linalg.cholesky(reg_corr)

        # 1. Generate uncorrelated standard normal variates
        Z = rng.standard_normal(size=(self.num_simulations, K))
        # 2. Correlate them
        Z_corr = np.dot(Z, L.T)
        # 3. Generate chi-square variates for Student-t copula scaling: W ~ chi2(nu) / nu
        chi2_samples = rng.chisquare(df=self.df_t, size=(self.num_simulations, 1))
        scale = np.sqrt(self.df_t / chi2_samples)
        # Student-t variates
        T_samples = Z_corr * scale

        # Scale by asset empirical volatilities
        simulated_returns = T_samples * std_devs

        # If a contagion stress shock is provided, shift the baseline return distribution
        if stress_shock:
            shock_vector = np.array([stress_shock.get(h, 0.0) for h in available_holdings], dtype=np.float64)
            simulated_returns += shock_vector

        # Portfolio simulated returns
        portfolio_sim_returns = np.dot(simulated_returns, avail_weights)

        # Losses are negative returns: loss = -return
        sim_losses = -portfolio_sim_returns

        # 95% and 99% Quantiles
        var_95 = float(np.percentile(sim_losses, 95.0))
        var_99 = float(np.percentile(sim_losses, 99.0))

        # Expected Shortfall (CVaR) = E[Loss | Loss >= VaR]
        cvar_95_losses = sim_losses[sim_losses >= var_95]
        cvar_99_losses = sim_losses[sim_losses >= var_99]
        cvar_95 = float(np.mean(cvar_95_losses)) if len(cvar_95_losses) > 0 else var_95
        cvar_99 = float(np.mean(cvar_99_losses)) if len(cvar_99_losses) > 0 else var_99

        # Baseline 60-day Gaussian VaR benchmark
        # Using last 60 days of historical returns
        recent_R = R[-60:] if len(R) >= 60 else R
        recent_port_returns = np.dot(recent_R, avail_weights)
        port_std = np.std(recent_port_returns)
        # Z for 99% normal is ~2.3263
        gaussian_var_99 = float(2.3263 * port_std)

        # Copula-to-Gaussian ratio: measures fat-tail amplification
        ratio = round(float(cvar_99 / max(gaussian_var_99, 1e-4)), 2)

        # Marginal risk contribution
        # Beta of asset i to portfolio simulated losses
        marginal_risks = {}
        port_loss_var = np.var(sim_losses) + 1e-8
        for i, h in enumerate(available_holdings):
            asset_loss = -simulated_returns[:, i]
            cov_i = np.cov(asset_loss, sim_losses)[0, 1]
            marginal_beta = cov_i / port_loss_var
            marginal_risks[h] = round(float(avail_weights[i] * marginal_beta * cvar_99), 4)

        return RiskMetricsResult(
            var_95=round(var_95, 4),
            var_99=round(var_99, 4),
            cvar_95=round(cvar_95, 4),
            cvar_99=round(cvar_99, 4),
            gaussian_var_99=round(gaussian_var_99, 4),
            copula_to_gaussian_ratio=ratio,
            num_simulations=self.num_simulations,
            asset_marginal_risks=marginal_risks
        )
