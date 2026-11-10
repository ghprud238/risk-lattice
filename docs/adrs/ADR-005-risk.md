# ADR-005: Tail Risk Simulation

## Status
Accepted

## Context
ContagionGraph architecture specification (Extended PRD v2.1 Section 29).

## Decision
Conditional Student-t Copula with shared radial chi-square scale, spectral PSD repair, and PCG64 seed=42.

## Revisit Trigger
Empirical transition to dynamic vine copula.

## Consequences
- Guarantees deterministic mathematical reproducibility and strict privacy separation.
- Prevents database deadlocks and accidental vendor lock-in.
