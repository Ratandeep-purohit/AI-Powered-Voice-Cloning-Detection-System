# Phase 03 — Analysis Session and Audio Intake Implementation

## Status

Implemented on branch `phase-03-analysis-session-audio-intake`.

## Implemented

- Authenticated analysis-session creation using the existing `calls` entity from Phase 01.
- Organization-scoped session creation and retrieval using the Phase 02 authenticated identity.
- RBAC for session creation and audio upload (`OPERATOR`, `SECURITY_ANALYST`, `ADMIN`, `SUPER_ADMIN`).
- Organization-scoped session listing and retrieval for authenticated users.
- Dedicated `audio_inputs` persistence model for upload metadata and storage references.
- Alembic migration for `audio_inputs`.
- Server-generated UUID-based storage keys; client filenames never determine storage paths.
- Configurable audio storage path, upload size, and allowed extensions.
- Streaming upload writes with SHA-256 calculation and configured size enforcement.
- Signature-based validation for WAV, MP3, OGG, FLAC, and M4A inputs.
- MIME-type and extension consistency checks.
- Empty-file rejection and path-traversal-safe filename normalization.
- Filesystem cleanup on validation or persistence failure.
- Audit events for session creation, accepted audio, and rejected audio.
- Minimal dashboard upload UI and frontend API client.
- Unit tests for audio signatures and filename safety.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/calls` | Create an upload analysis session. |
| GET | `/api/v1/calls` | List organization-scoped sessions. |
| GET | `/api/v1/calls/{call_id}` | Retrieve one organization-scoped session. |
| POST | `/api/v1/calls/{call_id}/audio` | Validate and register an audio upload. |

## Phase Boundary

Phase 03 stops after validated audio is stored and metadata is persisted. It does **not** perform decoding, normalization, segmentation, feature extraction, model inference, risk scoring, alerts, or prevention actions. Those responsibilities remain in later phases.

## Configuration

```text
AUDIO_STORAGE_PATH=storage/audio
AUDIO_MAX_UPLOAD_SIZE_MB=25
AUDIO_ALLOWED_EXTENSIONS=wav,mp3,ogg,flac,m4a
```

The upload size and allowed-format values are configuration defaults and can be changed without code changes.

## Validation

Run from `backend`:

```powershell
python -m pytest -q
alembic upgrade head
```

Run from `frontend`:

```powershell
npm run test
npm run build
npm run lint
```
