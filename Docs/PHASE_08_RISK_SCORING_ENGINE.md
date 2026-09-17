# Phase 08 — Risk Scoring Engine

## Status
Implementation complete; validation pending.

## Purpose
Phase 08 converts a completed `VoiceAnalysis` detector result into a deterministic, explainable, persisted `RiskScore` consumed by the Phase 07 Prevention & Response Engine.

Pipeline:

`Audio → Processing → AASIST → VoiceAnalysis → RiskScore → PreventionDecision`

Phase 08 does not retrain the model and does not replace AASIST inference.

## Deterministic scoring policy v1.0

Inputs:
- `synthetic_probability`
- `authentic_probability`
- `confidence`
- `detection_status`

The evidence score is:

`synthetic_probability * confidence + 0.5 * (1 - confidence)`

The persisted risk score is evidence score × 100, rounded to two decimals and bounded to 0–100.

Confidence therefore controls evidence strength. When confidence is low, the result moves toward the neutral midpoint instead of treating an uncertain detector result as strong spoof evidence.

Risk bands:

| Score | Risk level |
|---|---|
| 0–19.99 | SAFE |
| 20–39.99 | LOW |
| 40–59.99 | MEDIUM |
| 60–79.99 | HIGH |
| 80–100 | CRITICAL |

## Persistence

The existing `risk_scores` table is reused. Phase 08 stores:
- call ID
- VoiceAnalysis ID
- score
- risk level
- normalized contributing factors in JSONB
- scoring policy version
- calculated/created timestamps

A database unique constraint on `(voice_analysis_id, policy_version)` prevents duplicate scoring for the same analysis under the same policy version.

## Security

All reads and writes are tenant-scoped through:

`RiskScore/VoiceAnalysis → Call → organization_id == authenticated user organization_id`

A caller cannot score or retrieve an analysis belonging to another organization.

## API

### GET `/api/v1/risk/policy`
Returns the active scoring policy.

### POST `/api/v1/risk/calls/{session_id}/analyses/{analysis_id}/score`
Generates or reuses the deterministic risk score.

### GET `/api/v1/risk/calls/{session_id}/analyses/{analysis_id}/score`
Returns the persisted score for the active policy version.

Allowed write roles: `OPERATOR`, `SECURITY_ANALYST`, `ADMIN`, `SUPER_ADMIN`.

## Phase 07 integration

The Phase 07 `PreventionService` already consumes `RiskScore`. Phase 08 supplies the missing upstream producer; no risk calculation was added to Phase 07.

The response policy remains unchanged:

`SAFE/LOW → ALLOW`

`MEDIUM → MONITOR`

`HIGH → REQUIRE_REVIEW`

`CRITICAL → BLOCK`

## Validation

Run from `backend`:

```powershell
python scripts/validate_phase_08.py
```

Full 71k-sample ML evaluation remains intentionally out of scope for this policy/service validation gate.
