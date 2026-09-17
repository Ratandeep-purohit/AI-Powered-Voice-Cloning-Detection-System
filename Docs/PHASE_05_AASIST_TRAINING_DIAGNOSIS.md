# Phase 05 — AASIST Training Diagnosis

## Purpose

The full ASVspoof evaluation showed that the current checkpoint predicts almost everything as SPOOF and that REAL/SPOOF spoof-probability distributions overlap heavily. Threshold tuning alone cannot fix this. This diagnostic isolates the training behavior with a small, deterministic balanced experiment.

## What the diagnosis checks

1. ASVspoof train/dev integrity is validated before the experiment.
2. REAL=0 and SPOOF=1 label counts are reported.
3. A deterministic balanced subset is selected from train and dev.
4. Initial model predictions and spoof-probability statistics are measured before training.
5. Class-weight behavior is reported. A balanced smoke subset should produce weights `[1.0, 1.0]`.
6. A short AdamW training run records loss, F1, ROC-AUC, EER, prediction counts, score distributions, and gradient norm.
7. The before/after score separation can be compared without spending hours on a full 20-epoch run.

## Run

From `backend` with the project virtual environment active:

```powershell
python scripts/diagnose_aasist_training.py --dataset-root "E:\DataSet\LA" --samples-per-class 250 --epochs 3 --batch-size 4 --device cuda
```

The JSON report is written to:

```text
artifacts/evaluation/aasist/training_diagnosis.json
```

## How to interpret it

### Healthy learning signal

Look for:

- dev ROC-AUC moving materially above 0.50;
- EER moving downward;
- REAL spoof probabilities trending lower than SPOOF probabilities;
- predictions no longer collapsing to one class;
- training loss decreasing while balanced-dev metrics improve.

### Pipeline/model problem

If a balanced subset still produces near-random ROC-AUC, highly overlapping class scores, or one-class predictions after the short run, investigate preprocessing and architecture/input representation before another full training run.

### Overfitting signal

If balanced train metrics improve rapidly while balanced dev metrics stop improving or degrade, the model is learning the training subset but not generalizing. In that case the next step is regularization/data augmentation/model-capacity analysis rather than simply increasing epochs.

This experiment is diagnostic only; it does not replace the official ASVspoof evaluation.
