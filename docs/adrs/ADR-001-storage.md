# ADR-001: Storage Architecture

## Status
Accepted

## Context
ContagionGraph architecture specification (Extended PRD v2.1 Section 29).

## Decision
One native DuckDB owner process with immutable Parquet/binary artifacts.

## Revisit Trigger
Multiple API replicas requiring distributed transactions.

## Consequences
- Guarantees deterministic mathematical reproducibility and strict privacy separation.
- Prevents database deadlocks and accidental vendor lock-in.
