# ADR-009: Knowledge & Event Time Alignment

## Status
Accepted

## Context
ContagionGraph architecture specification (Extended PRD v2.1 Section 29).

## Decision
Explicit separation of knowledge cutoff dates and effective simulation times; unknown values flag warnings, not zero.

## Revisit Trigger
New global exchange trading calendar additions.

## Consequences
- Guarantees deterministic mathematical reproducibility and strict privacy separation.
- Prevents database deadlocks and accidental vendor lock-in.
