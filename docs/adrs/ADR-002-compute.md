# ADR-002: Pure Compute Isolation

## Status
Accepted

## Context
ContagionGraph architecture specification (Extended PRD v2.1 Section 29).

## Decision
Spawn pure functional compute kernels without database or network handles.

## Revisit Trigger
Distributed job scheduling redesign.

## Consequences
- Guarantees deterministic mathematical reproducibility and strict privacy separation.
- Prevents database deadlocks and accidental vendor lock-in.
