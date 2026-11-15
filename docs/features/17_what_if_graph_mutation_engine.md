# Feature 17: What-If Supply Chain Graph Mutation & Resilience ROI

## Executive Overview
When a stress test identifies an intolerable vulnerability (e.g. 100% of GPU silicon dependent on TSMC Fab 18), enterprise management faces strategic decisions:
- *"Should we invest \$2.5M to qualify TSMC's Phoenix, Arizona Fab 21?"*
- *"Should we spend \$1.2M to dual-source packaging through Intel Foundry Services (IFS)?"*

The **What-If Supply Chain Graph Mutation Engine** enables risk engineers to test hypothetical network interventions (severing edges, adding dual-sourcing edges, reweighting dependencies) and computes the exact **Resilience Return on Investment (Resilience ROI)**:
$$\text{Resilience ROI} = \frac{\Delta \text{PnL}}{\text{CapEx Investment}}$$

---

## Supported Graph Mutation Operations

1. **Sever Edge (`SEVER_EDGE`)**:
   - Sets edge weight $W_{ij} = 0.0$.
   - Models complete decoupling or vendor replacement (e.g., eliminating exposure to a sanction-threatened entity).
2. **Reweight Edge (`REWEIGHT_EDGE`)**:
   - Reduces dependency weight $W_{ij}$ to $W'_{ij} < W_{ij}$.
   - Models partial volume reallocation (e.g. re-routing 60% of wafer packaging to domestic facilities).
3. **Add Dual-Source Edge (`ADD_EDGE`)**:
   - Introduces a new transmission arc $W_{kj} > 0.0$ from alternative supplier $k$.
   - Models qualification of secondary suppliers (e.g. Intel or Samsung) to mitigate single-point concentration.

---

## Resilience ROI & Capital Relief Metrics

### 1. Avoided Stress Loss ($\Delta \text{PnL}$)
$$\Delta \text{PnL} = \text{Loss}_{\text{mutated}} - \text{Loss}_{\text{baseline}}$$
where $\Delta \text{PnL} > 0$ represents portfolio capital preserved during the crisis.

### 2. Resilience ROI
$$\text{ROI}_{\text{resilience}} = \frac{\Delta \text{PnL}}{\sum_{m} \text{CapEx}_m}$$
For example, if an intervention costs \$2.5M in tooling/qualification and reduces stress losses from -\$23.45M to -\$19.65M ($\Delta \text{PnL} = +\$3.80\text{M}$):
$$\text{Resilience ROI} = \frac{\$3.80\text{M}}{\$2.50\text{M}} = 1.52\times \quad (+152\%)$$

### 3. Regulatory Capital Relief
Reductions in 99% CVaR translate directly into lower regulatory capital surcharges under Basel III market risk frameworks:
$$\text{Capital Relief} = \text{CVaR}_{\text{baseline}} - \text{CVaR}_{\text{mutated}}$$

---

## Technical Implementation

### File Locations
- **Engine Core**: `backend/app/engine/mutation.py` (pure AST isolated)
- **Unit Tests**: `backend/tests/unit/test_liquidity_and_mutation.py`
- **API Endpoint**: `POST /api/v1/mutation/evaluate`
- **Frontend Component**: `frontend/src/components/SupplyChainMutationStudio.tsx`

---

## Verification & Test Coverage
- `backend/tests/unit/test_liquidity_and_mutation.py::test_what_if_graph_mutation_resilience_roi`
- `backend/tests/integration/test_expansion_services.py::test_mutation_evaluation_endpoint`
- `backend/tests/integration/test_boundary_and_engine.py::test_engine_ast_import_isolation`
