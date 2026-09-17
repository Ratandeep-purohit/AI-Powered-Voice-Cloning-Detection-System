# Phase 07 — Prevention & Response Engine Implementation

## Status

**Implementation complete; consolidated validation pending local execution.**

Phase 07 consumes an existing `RiskScore` and converts its validated risk level into a deterministic, auditable response decision. It does not re-run audio processing, AASIST inference, or risk scoring.

## Policy v1.0

| Risk level | Response action |
|---|---|
| SAFE | ALLOW |
| LOW | ALLOW |
| MEDIUM | MONITOR |
| HIGH | REQUIRE_REVIEW |
| CRITICAL | BLOCK |

`SAFE -> ALLOW` is explicitly supported because the existing Phase 06 database contract permits the `SAFE` level. No numeric risk thresholds are redefined in Phase 07.

## Architecture

```text
Completed RiskScore
      ↓
Tenant + input validation
      ↓
Response Policy v1.0
      ↓
Deterministic PreventionDecision
      ↓
PostgreSQL persistence
      ↓
AuditLog
      ↓
Authorized API response
```

## Implemented Components

- `backend/app/models/prevention_decision.py`
  - immutable response snapshot
  - organization/call/risk-score ownership fields
  - risk score and level snapshot
  - selected response action
  - policy version and human-readable reason
  - unique `(risk_score_id, policy_version)` constraint for deterministic idempotency
- `backend/alembic/versions/7c1d2e4f8a90_phase_07_prevention_decisions.py`
  - creates the prevention decision history table
- `backend/app/services/response_policy_service.py`
  - centralized policy mapping
  - policy validation
  - deterministic reason generation
- `backend/app/services/prevention_service.py`
  - tenant-scoped risk lookup
  - input validation
  - policy evaluation
  - decision persistence
  - audit event persistence
  - duplicate evaluation reuse
- `backend/app/schemas/prevention.py`
  - API response contracts
- `backend/app/api/v1/prevention.py`
  - `GET /api/v1/prevention/policy`
  - `POST /api/v1/prevention/calls/{session_id}/risk/{risk_score_id}`
  - `GET /api/v1/prevention/calls/{session_id}/risk/{risk_score_id}`
- `backend/app/main.py`
  - registers the Phase 07 router
- `backend/app/models/__init__.py`
  - registers the model for Alembic metadata discovery

## Security

The authenticated user's organization is used for every risk lookup and prevention decision. The client cannot select an authoritative organization context. Cross-tenant risk IDs therefore resolve as not found rather than leaking resource existence.

Prevention evaluation fails closed for invalid risk levels, invalid scores, missing risk assessments, and persistence errors. Evaluation failure is never converted into `ALLOW`.

## Audit

Successful new decisions create an append-oriented `AuditLog` event:

`PREVENTION / PREVENTION_DECISION_GENERATED`

The audit metadata records the call, risk result, risk score, risk level, response action, and policy version without storing raw audio.

## Idempotency

Repeated evaluation of the same risk result under policy v1.0 returns the existing `PreventionDecision`. This avoids duplicate response records and duplicate audit events for normal repeated requests.

Historical decisions retain the policy version and response explanation used at creation time.

## Testing

Focused tests cover:

- SAFE/LOW/MEDIUM/HIGH/CRITICAL mappings
- normalization of risk-level input
- invalid risk-level rejection
- policy configuration validation
- no hidden fallback action
- decision persistence
- audit persistence
- duplicate evaluation reuse
- cross-tenant isolation
- invalid score/level fail-closed validation
- API route registration
- unauthenticated API denial
- Phase 05/06 regression suites

## Validation Command

From `backend/`:

```powershell
python scripts/validate_phase_07.py
```

For the full backend regression suite as an optional final check:

```powershell
python scripts/validate_phase_07.py --pytest-all
```

Phase 07 does **not** run the 71,237-sample ML evaluation. That evaluation belongs to the final ML milestone and is intentionally not repeated for a policy-layer change.

## Definition of Done

Phase 07 is ready to mark complete after the consolidated validator reports:

```text
PHASE 07 VALIDATION PASSED
```

The validator also writes:

`backend/artifacts/evaluation/phase_07_validation.json`
