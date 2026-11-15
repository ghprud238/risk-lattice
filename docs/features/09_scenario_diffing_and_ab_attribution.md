# Feature 09: Scenario Diffing & A/B Risk Attribution Engine

## Executive Overview
Investment committees and risk oversight boards frequently need to compare alternative scenario variants:
- *"How does a full naval blockade compare against an air/maritime quarantine?"*
- *"What is the incremental portfolio impact if Foxconn maintains 60 days of inventory vs 30 days?"*

The **Scenario Diffing Engine** executes side-by-side comparative analysis of two scenarios ($A$ and $B$), decomposing the exact delta ($\Delta \text{PnL} = \text{PnL}_B - \text{PnL}_A$) across individual assets, network transmission hops, and marginal risk contributions.

---

## Mathematical Formulation

### 1. Element-wise Network Delta
For each network node $i \in \{1, \dots, N\}$:
$$\Delta s_i = s_i^{(B)} - s_i^{(A)}$$
$$\Delta \text{PnL}_i = \text{Notional}_i \cdot \Delta s_i$$

### 2. Hop-by-Hop Attribution Waterfall
The aggregate difference is partitioned by propagation hop:
$$\Delta \text{PnL} = \sum_{k=0}^4 \Delta \text{PnL}^{(\text{hop } k)}$$
This immediately isolates whether variance between scenarios is driven by the initial direct impulse ($\text{Hop } 0$) or downstream supply chain contagion amplification ($\text{Hop } 1 \dots 4$).

### 3. Euler / Shapley Marginal Attribution
The marginal percentage contribution of each asset $i$ to total scenario divergence:
$$\text{Attribution}_i = \frac{\Delta \text{PnL}_i}{\Delta \text{PnL}_{\text{total}}} \times 100\%$$

---

## Technical Implementation

### File Locations
- **Engine Core**: `backend/app/engine/diffing.py`
- **Unit Tests**: `backend/tests/unit/test_timeline_and_diff.py`
- **API Endpoint**: `POST /api/v1/scenario/diff`
- **Frontend Component**: `frontend/src/components/ScenarioDiffViewer.tsx`

### Frontend Features
- Side-by-side dropdown selectors for Scenario A and Scenario B.
- Dual-metric KPI comparison cards (Total Loss, 99% CVaR, Hop 1 Cascades).
- Colored Delta Waterfall chart showing which holdings saw worsened vs mitigated impact.
- Export diff analysis summary directly into executive memorandum.

---

## Verification & Test Coverage
- `backend/tests/unit/test_timeline_and_diff.py::test_scenario_diffing_engine`
- `backend/tests/integration/test_advanced_features_api.py::test_scenario_diff_api`
