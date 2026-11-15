# Feature 05: Safety Stock & Inventory Buffer Dynamics

## Executive Overview
A primary flaw in naive supply chain stress-testing models is treating input disruptions as instantaneous revenue collapses. In reality, modern corporations hold buffer inventory (days-of-inventory on hand, or DOI). If a Tier-1 supplier goes offline for 30 days, but an OEM maintains 45 days of safety stock, the OEM incurs zero production disruption during the first month.

RiskLattice incorporates a **Dynamic Inventory Absorption Model** directly into its network propagation kernel, dynamically dampening shock transmission based on reported Days-of-Inventory.

---

## Mathematical Formulation

### 1. Absorption Function
For a downstream company $j$ receiving a shock from supplier $i$, let:
- $S_{\text{gross}}$ be the gross unmitigated shock transmitted across edge $(i \to j)$.
- $\text{DOI}_j$ be company $j$'s on-hand days of inventory for component $i$.
- $T_{\text{shock}}$ be the duration of the external supply disruption in days.

The effective shock $S_{\text{eff}}$ transmitted downstream is:
$$S_{\text{eff}} = \max\left(0.0, \, S_{\text{gross}} \cdot \left(1.0 - \frac{\text{DOI}_j}{T_{\text{shock}}}\right)\right)$$

### 2. Edge-Cases & Regimes
1. **Full Absorption ($\text{DOI}_j \ge T_{\text{shock}}$)**:
   $$S_{\text{eff}} = 0.0$$
   The inventory buffer completely insulates production; zero cascade is transmitted to Tier-2/Tier-3 customers.
2. **Partial Absorption ($\text{DOI}_j < T_{\text{shock}}$)**:
   $$0 < S_{\text{eff}} < S_{\text{gross}}$$
   The shock is proportionally attenuated. For example, if disruption duration is 60 days and DOI is 45 days:
   $$\text{Attenuated Fraction} = 1.0 - \frac{45}{60} = 0.25 \implies S_{\text{eff}} = 0.25 \cdot S_{\text{gross}}$$
3. **Zero Buffer / Just-in-Time ($\text{DOI}_j = 0$)**:
   $$S_{\text{eff}} = S_{\text{gross}}$$
   Pure immediate transmission (typical of perishable goods or lean manufacturing).

---

## Technical Implementation

### File Locations
- **Engine Core**: `backend/app/engine/propagator.py`
- **Unit Tests**: `backend/tests/unit/test_inventory_buffer_propagation.py`
- **API Endpoint**: `POST /api/v1/stress/simulate`

### Code Architecture
```python
def compute_effective_shock_with_inventory(
    gross_shock: float,
    days_of_inventory: float,
    disruption_duration_days: float = 60.0
) -> float:
    if disruption_duration_days <= 0:
        return gross_shock
    buffer_ratio = min(1.0, max(0.0, days_of_inventory / disruption_duration_days))
    absorption_factor = 1.0 - buffer_ratio
    return gross_shock * absorption_factor
```

---

## Verification & Test Coverage
- `backend/tests/unit/test_inventory_buffer_propagation.py::test_complete_inventory_absorption` (verifies $S_{\text{eff}} = 0.0$ when $\text{DOI} \ge T$)
- `backend/tests/unit/test_inventory_buffer_propagation.py::test_partial_inventory_absorption` (verifies exact linear proportional attenuation)
- `backend/tests/unit/test_inventory_buffer_propagation.py::test_propagate_kernel_with_inventory_buffers` (verifies multi-hop propagation with heterogeneous inventory cushions across Apple, Ford, and Nvidia)
