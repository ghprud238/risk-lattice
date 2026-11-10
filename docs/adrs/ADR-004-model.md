# ADR-004: Multi-Hop Contagion & Distress

## Status
Accepted

## Context
ContagionGraph architecture specification (Extended PRD v2.1 Section 29).

## Decision
Exactly K=4 rounds with alpha=0.65 applied once per edge and non-linear signed distress.

## Revisit Trigger
Peer-reviewed versioned econometric propagation update.

## Consequences
- Guarantees deterministic mathematical reproducibility and strict privacy separation.
- Prevents database deadlocks and accidental vendor lock-in.
