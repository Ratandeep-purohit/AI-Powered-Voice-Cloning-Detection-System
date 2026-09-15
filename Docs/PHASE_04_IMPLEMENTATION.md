# Phase 04 — Audio Processing Pipeline

## Status

Implementation started on `phase-04-audio-processing-pipeline`.

## Scope

Phase 04 takes a validated `AudioInput` from Phase 03 and converts it into a deterministic, model-ready WAV representation. It does not perform AI inference, spoof detection, risk scoring, alerts, or prevention actions.

## Processing flow

```text
Validated AudioInput
        ↓
Secure storage lookup
        ↓
FFmpeg decode
        ↓
Channel standardization
        ↓
Sample-rate standardization
        ↓
16-bit PCM WAV
        ↓
Peak normalization
        ↓
Duration validation
        ↓
Processed audio storage
        ↓
AudioProcessingJob metadata
```

## Configuration

```text
AUDIO_PROCESSING_SAMPLE_RATE=16000
AUDIO_PROCESSING_CHANNELS=1
AUDIO_PROCESSING_MAX_DURATION_SECONDS=1800
AUDIO_PROCESSING_FFMPEG_BINARY=ffmpeg
```

The processing target is configurable so a future Phase 05 model can select a different compatible sample rate or channel layout without redesigning the pipeline.

## API

```text
POST /api/v1/calls/{session_id}/audio/{audio_input_id}/process
```

The endpoint requires the same analysis roles used by Phase 03 and enforces organization/session ownership before processing.

## Storage

Processed files are stored under the configured audio storage root in the `processed/` namespace with server-generated UUID filenames. Client filenames and storage references never become filesystem paths directly.

## Database

`audio_processing_jobs` stores:

- source sample rate/channels/duration
- processed sample rate/channels/duration
- processing status
- processed storage key
- processed file size and SHA-256
- whether peak normalization changed samples
- processing timestamps
- failure information

## Dependency

Phase 04 uses the `ffmpeg` executable for decoding and standardization. The executable must be installed on the runtime host and available on `PATH`, or configured through `AUDIO_PROCESSING_FFMPEG_BINARY`.

## Phase boundary

Audio segmentation/VAD and model inference are intentionally kept separate from this first implementation slice. Existing `AudioSegment` remains the Phase 04/05 integration point for chunk metadata; VAD/chunking policy should be aligned with the selected detection model before it is made authoritative.
