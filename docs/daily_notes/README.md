# Daily Engineering Notes Index

This directory maintains comprehensive daily engineering logs documenting the architectural decisions, implementation milestones, debugging procedures, and verification results for **RiskLattice** (formerly ContagionGraph).

---

## Log Entries

| Date | Title | Key Topics Covered | Commits |
| :--- | :--- | :--- | :--- |
| [**2026-11-10**](./2026-11-10.md) | **System Architecture, Core Implementation, and Expanded PRD v2.1 Verification** | Project setup, Milestones 1–4, DuckDB schema, Huber calibrator, 4-hop propagation, Student-$t$ Copula, LiteLLM router, verbatim 10-K extraction, privacy firewall (Rule P-01), FastAPI SSE, Next.js 15 UI, Expanded PRD v2.1 compliance, AST engine isolation, analytical suites ($N\text{-}01$–$N\text{-}12$, $R\text{-}01$–$R\text{-}08$, $P\text{-}01$–$P\text{-}05$), Minsky bridge, CLI diagnostics (`doctor.py`, `smoke_test.py`), and ADRs 001–010. | `ff96151`<br>`a3ae69c`<br>`45b15fd`<br>`94b51ac`<br>`d29abbc` |
| [**2026-11-11**](./2026-11-11.md) | **Operational Architecture, Rebranding to RiskLattice, Data Flows, Debugging, & Core Algorithms** | Conceptual purpose, neuro-symbolic division of labor, Taiwan Foundry walkthrough, 5-tier debugging manual, Next.js UI guide, project rebranding to RiskLattice, 5 layers of fragility, input/output spec, executive plain-English translation layer, and two-phase core algorithms (Damped Propagator & Student-$t$ Copula). | `d29abbc`<br>`021acf1`<br>`0a75466`<br>`66ca1ff`<br>`80c025e`<br>`191e3e3`<br>`cda87b7`<br>`bc8025a` |

---

## Quick Links

- [Root README](../../README.md)
- [Architecture Decision Records (ADRs)](../adrs/)
- [Backend Diagnostics Script](../../backend/scripts/doctor.py)
- [Fast Offline Smoke Test](../../backend/scripts/smoke_test.py)
