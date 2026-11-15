# Feature 02: Student-t Copula Tail-Risk & CVaR Engine

## Executive Overview
Traditional risk systems (like RiskMetrics) rely on standard multivariate normal assumptions, drastically underestimating joint tail events. During crises, correlations jump to 1.0, and assets experience joint heavy-tailed crashes. RiskLattice uses a multivariate **Student-$t$ Copula** with low degrees of freedom ($\nu = 4.0$) and Higham Positive Semi-Definite (PSD) matrix repair to accurately capture non-linear joint tail risk and compute 99% Conditional Value at Risk (Expected Shortfall).

---

## Mathematical Formulation

### 1. Multivariate Student-$t$ Distribution
A random vector $X \in \mathbb{R}^d$ follows a Student-$t$ distribution with $\nu$ degrees of freedom, mean vector $\mu$, and dispersion matrix $\Sigma$:
$$X = \mu + \sqrt{\frac{\nu}{S}} \cdot Z$$
where $Z \sim \mathcal{N}(0, \Sigma)$ and $S \sim \chi^2(\nu)$ is independent of $Z$.

The parameter $\nu = 4.0$ creates fat tails with infinite fourth moment (kurtosis), matching empirical financial crash dynamics observed during the 2008 GFC, 2020 COVID shock, and 2022 supply chain squeezes.

### 2. Higham (2002) PSD Matrix Repair
Empirical correlation matrices estimated under stress frequently violate Positive Semi-Definiteness (PSD) due to missing data or asynchronous trading. The engine applies Nick Higham's alternating projection algorithm:
$$\min_{\Sigma \succeq 0, \text{diag}(\Sigma)=1} \|\Sigma - \Sigma_{\text{raw}}\|_F$$
This guarantees stable Cholesky factorization $\Sigma = L L^T$ without throwing eigenvalue decomposition errors.

### 3. Joint Tail Dependence Coefficient
Unlike Gaussian copulas where tail dependence $\lambda_U = \lambda_L = 0$ asymptotically, the Student-$t$ copula possesses strictly positive tail dependence:
$$\lambda = 2 \cdot t_{\nu+1}\left(-\sqrt{\frac{(\nu+1)(1-\rho)}{1+\rho}}\right) > 0$$
This forces clustered co-crashes when macro factors deteriorate.

### 4. Downside Risk Metrics
From 10,000 simulated portfolio loss paths $\{L^{(m)}\}_{m=1}^M$:
- **Value at Risk (95% VaR)**:
  $$\text{VaR}_{0.95} = \inf \{ l : \mathbb{P}(L > l) \le 0.05 \}$$
- **Conditional Value at Risk (99% CVaR / Expected Shortfall)**:
  $$\text{CVaR}_{0.99} = \mathbb{E}[L \mid L \ge \text{VaR}_{0.99}]$$
CVaR satisfies subadditivity, making it a coherent risk measure per Artzner et al. (1999).

---

## Technical Implementation

### File Locations
- **Engine Core**: `backend/app/engine/risk_metrics.py`
- **Unit Tests**: `backend/tests/unit/test_copula_cases.py` (Tests R01 to R08)
- **API Endpoint**: `POST /api/v1/stress/simulate`

### Code Architecture
```python
import numpy as np
from scipy import stats

class TailRiskEngine:
    def __init__(self, df_t: float = 4.0, num_simulations: int = 10000, seed: int = 42):
        self.df_t = df_t
        self.num_simulations = num_simulations
        self.seed = seed

    def compute_cvar(self, returns: np.ndarray, weights: np.ndarray, notional: float) -> dict:
        rng = np.random.default_rng(self.seed)
        # Cholesky decomposition of PSD-repaired covariance matrix
        cov = np.cov(returns, rowvar=False)
        cov_psd = self.repair_psd(cov)
        L = np.linalg.cholesky(cov_psd)
        
        # Student-t sampling: Z / sqrt(S / nu)
        Z = rng.standard_normal((self.num_simulations, len(weights)))
        S = rng.chisquare(self.df_t, size=(self.num_simulations, 1))
        scale = np.sqrt(self.df_t / S)
        t_samples = scale * (Z @ L.T)
        
        portfolio_losses = -notional * (t_samples @ weights)
        var_95 = float(np.percentile(portfolio_losses, 95))
        var_99 = float(np.percentile(portfolio_losses, 99))
        cvar_99 = float(portfolio_losses[portfolio_losses >= var_99].mean())
        
        return {"var_95": var_95, "var_99": var_99, "cvar_99": cvar_99}
```

---

## Verification & Test Coverage
- `backend/tests/unit/test_copula_cases.py::test_r01_shared_radial_t_scale` (verifies shared radial scaling factor)
- `backend/tests/unit/test_copula_cases.py::test_r02_psd_repair` (verifies positive definiteness and unit diagonals)
- `backend/tests/unit/test_copula_cases.py::test_r04_hand_ranked_metrics_es_ge_var` (proves $\text{ES}_{0.99} \ge \text{VaR}_{0.99}$)
- `backend/tests/test_math.py::test_kupiec_pof_validation` (Kupiec Proportion of Failures backtest validation)
