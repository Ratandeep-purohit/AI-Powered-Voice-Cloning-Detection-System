# Consolidated Phase Validation Workflow

## Purpose

The project should not repeatedly run the full ASVspoof Eval split after every small code change. The full Eval split contains 71,237 samples, so it is reserved for a phase-completion/final validation run.

During development, use fast tests and smoke checks. Once a phase is complete, run one consolidated validation command.

## Phase 06

From `backend/`:

```powershell
python scripts/validate_phase_06.py --dataset-root "E:\DataSet\LA" --device cuda
```

The default gate runs:

1. ASVspoof train/dev/eval integrity validation.
2. Phase 05/06 ML + inference pytest suite.
3. Python compile check.
4. Real AASIST checkpoint loading.
5. Real checkpoint inference smoke test on a deterministic temporary WAV.
6. A JSON validation report at `artifacts/evaluation/phase_06_validation.json`.

The expensive full 71,237-sample Eval inference is intentionally **not** run by default.

## Final Phase 06 validation

When code and configuration are frozen:

```powershell
python scripts/validate_phase_06.py --dataset-root "E:\DataSet\LA" --device cuda --pytest-all --full-eval
```

This runs the complete backend test suite and then the held-out Eval inference using the frozen DEV-derived threshold (`0.5977`).

## Development rule for future phases

Use this pattern:

```text
Build the entire phase
        ↓
Run focused tests while developing
        ↓
Finish all phase code + docs
        ↓
Run one consolidated phase validation command
        ↓
Run expensive/full dataset evaluation only once when required
        ↓
Freeze the phase
```

Do not make a full-dataset evaluation a prerequisite for every tiny source/config change.
