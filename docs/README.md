# ContagionGraph Documentation Hub

Welcome to the engineering documentation for **ContagionGraph**, a hybrid neuro-symbolic financial stress-testing platform.

---

## Directory Navigation

- [**Daily Engineering Notes**](./daily_notes/README.md): Chronological record of all project interactions, implementations, data flow walkthroughs, debugging guides, and milestones.
  - [**2026-11-10: System Architecture & Implementation**](./daily_notes/2026-11-10.md): Complete record of Milestones 1–4 and Expanded PRD v2.1 implementation.
  - [**2026-11-11: Operations, Data Flow & Debugging Manual**](./daily_notes/2026-11-11.md): End-to-end Taiwan Foundry case walkthrough, 5-tier debugging protocol, and UI guide.
- [**Architecture Decision Records (ADRs)**](./adrs/): Formal records of core architectural and technical decisions.
  - [ADR-001: Embedded DuckDB Storage](./adrs/ADR-001-storage.md)
  - [ADR-002: Pure Compute Isolation for Engine](./adrs/ADR-002-compute.md)
  - [ADR-003: 4-Hop Damped Contagion Propagation](./adrs/ADR-003-graph.md)
  - [ADR-004: Huber Loss Robust Linear Calibration](./adrs/ADR-004-model.md)
  - [ADR-005: 10,000-Path Student-t Copula Simulation](./adrs/ADR-005-risk.md)
  - [ADR-006: Neuro-Symbolic Boundary & Privacy Firewall](./adrs/ADR-006-ai.md)
  - [ADR-007: Python Subprocess Minsky Integration](./adrs/ADR-007-native.md)
  - [ADR-008: Next.js 15 & FastAPI Deployment](./adrs/ADR-008-deploy.md)
  - [ADR-009: Snapshot-Based Time & Decay Model](./adrs/ADR-009-time.md)
  - [ADR-010: Server-Side PDF Report Generation](./adrs/ADR-010-pdf.md)

---

## Key Engineering Protocols

### 1. Diagnostics & Verification
```bash
# System environment & database health check
python backend/scripts/doctor.py

# Sub-second offline math smoke test (0.092s)
python backend/scripts/smoke_test.py

# Privacy firewall red-team audit (Rule P-01)
python backend/scripts/verify_privacy.py

# Full test suite (48 tests across unit, integration, math, llm, api)
pytest backend/tests/unit/ backend/tests/integration/ backend/tests/test_math.py backend/tests/test_llm.py backend/tests/test_api.py -v
```

### 2. Local Startup
```bash
# Run both Backend (FastAPI :8000) and Frontend (Next.js :3000)
./start.sh
```
