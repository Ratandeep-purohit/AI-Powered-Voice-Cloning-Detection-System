# Phase 06 — AASIST Detection Integration

## Purpose

Phase 06 connects the trained project AASIST-family detector to the existing application audio pipeline.

```text
POST /calls
    -> POST /calls/{session_id}/audio
    -> POST /calls/{session_id}/audio/{audio_input_id}/process
    -> POST /calls/{session_id}/audio/{audio_input_id}/detect
    -> VoiceAnalysis + audit event
```

The detector runs only on successfully processed 16 kHz, mono, 16-bit PCM WAV audio. The application reuses the same deterministic 4-second model-input preprocessing used by training/evaluation.

## Runtime checkpoint

The default runtime checkpoint is:

```text
backend/artifacts/checkpoints/aasist_balanced/best.pt
```

The checkpoint is intentionally ignored by Git. It must exist on the machine running the backend.

Configuration:

```text
AASIST_CHECKPOINT_PATH=artifacts/checkpoints/aasist_balanced/best.pt
AASIST_MODEL_NAME=AASIST-family spoof detector
AASIST_MODEL_VERSION=balanced-v1
AASIST_TARGET_DURATION_SECONDS=4.0
AASIST_DETECTION_THRESHOLD=0.5
```

The threshold currently defaults to `0.5` only as an integration-safe placeholder. It must not be described as the final production threshold. The operating threshold should be selected from the DEV split and then frozen before the independent Eval measurement.

## API

```text
POST /api/v1/calls/{session_id}/audio/{audio_input_id}/detect
```

The endpoint:

1. enforces organization ownership;
2. requires a successfully completed `AudioProcessingJob`;
3. loads the configured AASIST checkpoint;
4. converts the processed WAV into a floating-point tensor;
5. applies deterministic 4-second crop/pad and normalization;
6. runs inference with CUDA AMP when CUDA is available;
7. calculates REAL and SPOOF probabilities;
8. applies the configured decision threshold;
9. persists a `VoiceAnalysis` record;
10. writes an audit event.

Response contains the persisted analysis, decision, and threshold used.

## Security boundaries

- Processed storage keys are resolved under the configured audio storage root; path traversal is rejected.
- Detection is tenant-scoped through the call's organization ownership.
- The model checkpoint is a local runtime artifact; no third-party inference API or API key is used.
- The detector does not accept an arbitrary filesystem path from the API caller.

## Current ML result

The balanced checkpoint was evaluated on the full ASVspoof 2019 LA Eval split with ROC-AUC `0.8873` and EER `0.1835`. These are evaluation measurements, not a claim of production readiness.

## Validation

Run:

```powershell
cd E:\projects\AI-Powered-Voice-Cloning-Detection-Prevention-System\backend
python -m pytest tests/test_aasist_inference.py -v
```

For a real detector smoke test, ensure the balanced `best.pt` checkpoint is present under `backend/artifacts/checkpoints/aasist_balanced/`, start the backend, create an analysis call, upload an audio file, process it, then invoke the detection endpoint.
