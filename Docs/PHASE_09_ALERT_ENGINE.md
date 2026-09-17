# Phase 09 — Alert Engine

## Purpose

Convert persisted `RiskScore` results into tenant-scoped, deterministic security alerts and provide a complete alert lifecycle with append-only `AlertAction` history.

## Flow

`RiskScore → Alert Policy → Alert → AlertAction → Dashboard/WebSocket consumers`

## Policy v1.0

- SAFE / LOW: no security alert is generated.
- MEDIUM: `MEDIUM` alert.
- HIGH: `HIGH` alert.
- CRITICAL: `CRITICAL` alert.

Alert generation is idempotent per `(risk_score_id, policy_version)`.

## Lifecycle

`OPEN → ACKNOWLEDGED → INVESTIGATING → RESOLVED`

`OPEN → DISMISSED`

`ACKNOWLEDGED → DISMISSED`

`INVESTIGATING → DISMISSED`

Resolved/dismissed alerts are terminal.

## Security

All reads and writes are organization-scoped. Write operations require OPERATOR, SECURITY_ANALYST, ADMIN, or SUPER_ADMIN. Every lifecycle transition creates an append-only `AlertAction` and a corresponding audit event.

## Scope

Phase 09 does not perform audio processing, AASIST inference, or risk scoring. It consumes the existing `RiskScore` produced by Phase 08.
