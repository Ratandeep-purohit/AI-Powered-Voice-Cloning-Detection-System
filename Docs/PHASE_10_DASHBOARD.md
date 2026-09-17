# Phase 10 — Security Dashboard APIs + Frontend

## Purpose

Phase 10 turns the completed detection → risk → policy → alert pipeline into an analyst-facing security console. The dashboard is a read/presentation layer: it does not change model output, risk scores, prevention decisions, or alert policy.

## Backend

### Endpoint

`GET /api/v1/dashboard/overview`

Authentication is required. The response is always scoped to the authenticated user's `organization_id`.

### Overview payload

- organization identity
- six dashboard metrics
- seven-day activity trend
- risk-level distribution
- recent alerts
- recent detector analyses
- active alert count
- critical active alert count
- blocked policy-action count
- server-side generation timestamp

### Metrics

- Analysis sessions — last 7 days, with comparison against the preceding 7 days when available.
- Completed detector runs.
- Spoof detections using the frozen Phase 06 detector threshold (`0.5977`).
- Average deterministic risk score.
- Active alerts (`OPEN`, `ACKNOWLEDGED`, `INVESTIGATING`).
- Policy `BLOCK` outcomes.

### Security boundary

The service queries existing tenant-owned `Call`, `VoiceAnalysis`, `RiskScore`, `PreventionDecision`, `Alert`, and `Organization` records. It does not expose cross-tenant records and does not add a new database table or migration.

## Frontend

The existing authenticated `/dashboard` route is upgraded into the Phase 10 Security Console using the existing React + TypeScript + Vite stack.

### Experience

- compact analyst sidebar
- sticky search/header area
- live security status indicator
- animated overview hero
- animated metric cards
- seven-day activity visualization using lightweight SVG
- risk distribution bars
- recent alert queue
- latest detector feed
- existing secure audio-intake workflow retained
- decision-pipeline visualization
- responsive tablet/mobile layout
- reduced-motion accessibility fallback
- 30-second silent dashboard refresh plus manual refresh

### Visual direction

The visual language is deliberately product-oriented rather than decorative AI art:

- white surfaces
- soft blue, violet, mint, amber and rose accents
- restrained borders and shadows
- high readability
- small radii and compact information density
- motion used for hierarchy and feedback, not noise

No charting dependency is introduced for this phase; the activity chart is rendered with SVG/CSS so the dashboard remains lightweight.

## Validation

From `backend`:

```powershell
python scripts/validate_phase_10.py
```

Frontend:

```powershell
cd ../frontend
npm run test
npm run build
npm run lint
```

Full ML evaluation is intentionally outside the Phase 10 validation gate.
