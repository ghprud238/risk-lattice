# Feature 08: Multi-Period Dynamic Timeline Simulation (0-90 Days)

## Executive Overview
Supply chain shocks do not unfold in a single instantaneous step; they evolve dynamically across distinct time horizons:
- **Day 0 - 7**: Initial shock shockwave, physical shutdown, port blockade.
- **Day 7 - 30**: Inventory buffers cushion production; emergency air freight rerouting.
- **Day 30 - 60**: Safety stocks run dry; production line halts; component rationing.
- **Day 60 - 90**: Full secondary distress cascades, quarterly revenue guidance warnings, credit rating downgrades.

The **Multi-Period Timeline Engine** simulates this trajectory at discrete milestones ($T \in \{0, 7, 14, 30, 60, 90\}$ days) with interactive timeline scrub controls in the frontend.

---

## Mathematical Formulation

### Discrete-Time Dynamic Propagation
For time step $t \in \{0, 7, 14, 30, 60, 90\}$:
$$s_i(t) = s_i(t - \Delta t) + \Delta s_i^{\text{inflow}}(t) - \text{Recovery}_i(t)$$
where:
1. **Lead-Time Lag**:
   An edge from $j$ to $i$ with maritime transit lead-time $\tau_{ji}$ (e.g. 21 days from Kaohsiung to Long Beach) transmits zero incremental disruption until $t \ge \tau_{ji}$.
2. **Buffer Depletion Rate**:
   $$\text{RemainingBuffer}_i(t) = \max\left(0, \text{DOI}_i - t\right)$$
3. **Cumulative Portfolio Loss**:
   $$L(t) = \sum_{i=1}^N w_i \cdot s_i(t) \cdot \text{PortfolioNotional}$$

---

## Technical Implementation

### File Locations
- **Engine Core**: `backend/app/engine/timeline.py`
- **Unit Tests**: `backend/tests/unit/test_timeline_and_diff.py`
- **API Endpoint**: `POST /api/v1/timeline/simulate`
- **Frontend Component**: `frontend/src/components/TimelinePlayer.tsx`

### Frontend Features
- Play / Pause animation scrubbing through the 90-day trajectory.
- Milestone step buttons ($T=0, 7, 14, 30, 60, 90$).
- Dynamic line charts showing portfolio drawdown deepening as days-of-inventory are depleted.
- Critical inflection alerts (e.g., "Day 32: Apple iPhone 17 inventory buffer exhausted; production idle begins").

---

## Verification & Test Coverage
- `backend/tests/unit/test_timeline_and_diff.py::test_multi_period_timeline_progression` (verifies monotonic drawdown progression as time increases)
- `backend/tests/integration/test_advanced_features_api.py::test_timeline_simulation_api`
