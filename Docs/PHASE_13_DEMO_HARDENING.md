# Phase 13 — Testing + Demo Hardening

## Objective

Prepare the completed voice-security workflow for a repeatable hackathon/demo presentation without changing the ML model, frozen detection threshold, deterministic risk policy, prevention policy, alert lifecycle, or tenant-isolation rules.

## Demo-readiness gate

Run from the repository root after Phase 12 validation has passed:

```powershell
cd backend
python scripts/validate_phase_13.py
```

The gate checks:

- Backend application and end-to-end pipeline files exist.
- Phase 12 regression gate is present.
- The configured production AASIST checkpoint exists.
- FFmpeg is available and executable.
- Required health, analysis, end-to-end analysis, and WebSocket routes are registered.
- Optional authentic/synthetic demo audio paths are present when configured.
- The frontend package exposes `build`, `test`, and `lint` validation scripts.
- A frontend production build exists at `frontend/dist/index.html`.

## Demo audio configuration

The gate accepts these optional environment variables:

- `DEMO_AUTHENTIC_AUDIO_PATH`
- `DEMO_SYNTHETIC_AUDIO_PATH`

Both should point to prepared, authorized demo samples before a presentation. The validator does not require them so the repository remains portable and does not contain sensitive audio.

## Operator rehearsal

Before presenting:

1. Pull the latest `main`.
2. Start PostgreSQL and verify the backend can reach it.
3. Start the FastAPI backend.
4. Start the React frontend used for the presentation.
5. Run the Phase 12 regression gate.
6. Run the Phase 13 readiness gate.
7. Confirm the AASIST checkpoint loads on the actual demo machine.
8. Confirm one authentic and one authorized synthetic sample can complete the end-to-end pipeline.
9. Confirm the dashboard receives the alert and WebSocket updates.
10. Keep a prepared result available as a declared fallback, not as a simulated claim of fresh inference.

## Failure handling

- **ML/checkpoint failure:** stop the live inference segment and show the prepared result while explicitly identifying it as prepared.
- **FFmpeg failure:** use an already processed authorized sample only if that fallback is prepared and documented.
- **WebSocket failure:** continue using REST retrieval; live push is an enhancement, not a prerequisite for explaining the deterministic workflow.
- **Database failure:** switch to the prepared local backup environment; do not silently present stale data as a live result.
- **Frontend failure:** use a prepared backup tab or recording and continue the verbal system walkthrough.
- **Copilot failure:** skip the optional advisory segment and continue with detection, risk, policy, alert, and investigation.

## Presenter safety rules

- Use only self-generated, publicly permitted, or explicitly authorized audio.
- Do not clone or impersonate a real person without authorization.
- Do not expose passwords, JWT secrets, database credentials, private keys, or environment files on screen.
- Do not describe an ML score as proof of authenticity or fraud.
- Keep prepared fallback results clearly labeled as prepared.
- The LLM/Copilot must remain advisory and cannot override deterministic security controls.

## Completion criteria

- [x] Phase 12 regression gate passes.
- [x] Backend compile check passes.
- [x] Frontend production build passes.
- [x] Frontend tests pass.
- [x] Frontend lint has zero errors.
- [ ] Phase 13 readiness gate passes on the presentation machine.
- [ ] Authentic demo sample rehearsed end-to-end.
- [ ] Authorized synthetic demo sample rehearsed end-to-end.
- [ ] Fallback path rehearsed.

Phase 13 is complete when the readiness gate and the operator rehearsal checklist are both satisfied.
