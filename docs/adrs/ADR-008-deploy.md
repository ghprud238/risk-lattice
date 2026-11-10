# ADR-008: Deployment Profiles

## Status
Accepted

## Context
ContagionGraph architecture specification (Extended PRD v2.1 Section 29).

## Decision
Native local development and Docker Compose with loopback bindings; optional single-replica K8s.

## Revisit Trigger
Multi-tenant cloud infrastructure scaling.

## Consequences
- Guarantees deterministic mathematical reproducibility and strict privacy separation.
- Prevents database deadlocks and accidental vendor lock-in.
