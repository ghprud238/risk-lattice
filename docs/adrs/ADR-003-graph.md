# ADR-003: Graph Kernel & Orientation

## Status
Accepted

## Context
ContagionGraph architecture specification (Extended PRD v2.1 Section 29).

## Decision
Sparse CSR / typed channel kernel with W[target, source] orientation.

## Revisit Trigger
Alternative graph query engine integration.

## Consequences
- Guarantees deterministic mathematical reproducibility and strict privacy separation.
- Prevents database deadlocks and accidental vendor lock-in.
