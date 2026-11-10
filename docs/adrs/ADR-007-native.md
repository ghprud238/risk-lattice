# ADR-007: Minsky Simulator Integration

## Status
Accepted

## Context
ContagionGraph architecture specification (Extended PRD v2.1 Section 29).

## Decision
Minsky is an optional, independent subprocess capability with isolated ABI probe.

## Revisit Trigger
Host package bundling license review.

## Consequences
- Guarantees deterministic mathematical reproducibility and strict privacy separation.
- Prevents database deadlocks and accidental vendor lock-in.
