# Feature 11: Four-Eyes Governance & Audit Vault

## Executive Overview
Under Federal Reserve SR 11-7 (Supervisory Guidance on Model Risk Management) and Basel III standards, high-stakes quantitative stress simulations cannot be executed or modified unilaterally. 

The **Four-Eyes Audit Vault** enforces a strict dual-key approval lifecycle: every scenario draft, portfolio version, and simulation run is cryptographically sealed with a SHA-256 manifest hash and requires independent secondary sign-off from a Chief Risk Officer or authorized Compliance Lead before being promoted to `APPROVED` status.

---

## The Four-Eyes Lifecycle

```
[DRAFT] ---> (Submit for Review) ---> [UNDER_REVIEW] ---> (Secondary Sign-off) ---> [APPROVED]
                                             |
                                             v (Reject with comments)
                                         [REJECTED]
```

### 1. Cryptographic Run Manifest
Every simulation run produces an immutable `RunManifest` containing:
- `run_id`: Unique UUID v4 identifier.
- `portfolio_hash`: SHA-256 fingerprint of normalized holdings and notional amounts.
- `graph_hash`: SHA-256 fingerprint of the 50-node calibrated supply chain adjacency matrix.
- `seed`: Deterministic PRNG seed used for Monte Carlo path generation.
- `engine_version`: Exact commit hash of the Python calculation kernel.
- `manifest_signature`: SHA-256 hash combining all preceding fields.

### 2. Dual-Key Separation of Duties
- **Submitter (First Eye)**: A Risk Analyst or Portfolio Manager who creates the scenario, sets direct impulse shocks, and runs preliminary simulations.
- **Approver (Second Eye)**: A Chief Risk Officer or Compliance Officer who verifies methodological soundess, checks risk appetite limit breaches, and signs off.
- **Rule Enforcement**: The system strictly prevents the submitter from approving their own draft (`assert submitter_id != approver_id`).

---

## Technical Implementation

### File Locations
- **Service Core**: `backend/app/services/audit_vault_service.py`
- **Unit Tests**: `backend/tests/unit/test_audit_vault.py`
- **API Endpoints**:
  - `POST /api/v1/governance/signoff`
  - `GET /api/v1/governance/status/{run_id}`
- **Frontend Component**: `frontend/src/components/RegulatorySignoffModal.tsx`

### Signoff Request Schema
```json
{
  "run_id": "run-citadel-202611-001",
  "reviewer_name": "Elena Rostova",
  "reviewer_role": "CHIEF_RISK_OFFICER",
  "decision": "APPROVED",
  "review_comments": "Verified 4-hop propagation and Almgren-Chriss liquidity parameters against SEC 10-K filings. Approved for Board Risk Committee submission."
}
```

---

## Verification & Test Coverage
- `backend/tests/unit/test_audit_vault.py::test_four_eyes_signoff_lifecycle_and_security` (verifies unauthorized role rejection and prevents self-approval)
- `backend/tests/integration/test_advanced_features_api.py::test_audit_governance_and_executive_report_api`
