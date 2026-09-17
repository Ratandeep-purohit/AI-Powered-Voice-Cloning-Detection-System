# Phase 11 — Real-Time Security Experience

## Goal

Add an authenticated WebSocket event channel so the security workspace can receive live analysis and alert events without polling.

## Delivered

- Tenant-scoped WebSocket endpoint: `GET`-style HTTP path upgrade at `/api/v1/realtime/ws` using an authenticated access token.
- `connection.ready` and heartbeat events.
- Tenant-isolated in-process connection manager.
- Live analysis event contract:
  - `analysis.started`
  - `analysis.processing_completed`
  - `analysis.detection_completed`
  - `analysis.risk_scored`
  - `analysis.prevention_decided`
  - `alert.created`
  - `analysis.completed`
  - `analysis.failed`
- Dedicated authenticated pipeline endpoint:
  - `POST /api/v1/calls/{session_id}/audio/{audio_input_id}/analyze-realtime`
- Existing `/analyze` endpoint remains unchanged for backward compatibility.
- Frontend WebSocket client and persistent workspace `Live`/`Offline` indicator.
- Tenant isolation tests for the event manager.
- Consolidated Phase 11 validation script.

## Event model

Every server event carries an event id, event type, organization id, optional analysis session id, UTC timestamp, and an event-specific payload.

## Security model

The WebSocket validates the same signed access JWT used by the REST API and loads the user with the JWT subject + organization pair. Connections are stored by organization, and events are only published to connections belonging to the same organization.

The browser currently supplies the short-lived access token as the WebSocket `token` query parameter because the frontend intentionally keeps the access token memory-only and the refresh token is an HttpOnly cookie. Production traffic must use TLS (`wss://`).

## Scaling boundary

The manager is deliberately process-local for the MVP. A multi-worker/horizontally scaled deployment should replace its internal connection registry with Redis/pub-sub or another shared event broker. The event schema and endpoint contract are kept stable so that this can be introduced without changing the product event model.

## Validation

From `backend/`:

```powershell
python scripts/validate_phase_11.py
```

Frontend:

```powershell
cd ..\frontend
npm run build
npm run test
npm run lint
```

Full ML evaluation remains intentionally out of scope for Phase 11.
