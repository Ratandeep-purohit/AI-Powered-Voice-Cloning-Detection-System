# Phase 05 — AASIST Threshold & Score Analysis

## Purpose

The full ASVspoof2019 LA Eval run showed a strong class-imbalance effect at the default argmax/0.5 decision boundary: the trained checkpoint predicted every REAL sample as SPOOF while missing only one SPOOF sample.

This stage separates two questions:

1. **Does the checkpoint produce useful score separation?**
2. **Which decision threshold gives a sensible operating point?**

Threshold tuning is performed on the `dev` split by default. The `eval` split remains an independent final measurement and must not be used to choose the production threshold.

## What is analyzed

For the SPOOF probability score:

- REAL and SPOOF score distributions
- minimum, maximum, mean and percentile statistics
- threshold sweep from 0.00 to 1.00 by default in 0.01 steps
- Accuracy
- Balanced accuracy
- Precision
- Recall / true-positive rate
- F1
- FAR (false-accept rate: REAL classified as SPOOF)
- FRR (false-reject rate: SPOOF classified as REAL)
- TN / FP / FN / TP
- score-based operating points for F1, balanced accuracy and EER

The analyzer does **not** change the checkpoint and does **not** automatically promote a threshold to production.

## Run on Dev

From `backend/`:

```powershell
python scripts/analyze_aasist_threshold.py --dataset-root "E:\DataSet\LA" --checkpoint "artifacts\checkpoints\aasist\best.pt" --split dev --batch-size 2 --device cuda
```

Expected runtime is much shorter than the full Eval run because Dev contains 24,844 samples rather than 71,237.

The report is written to:

```text
backend/artifacts/evaluation/aasist/threshold_analysis.json
```

## Optional grid changes

For a coarser first pass:

```powershell
python scripts/analyze_aasist_threshold.py --dataset-root "E:\DataSet\LA" --checkpoint "artifacts\checkpoints\aasist\best.pt" --split dev --batch-size 2 --device cuda --grid-step 0.05
```

The exact operating-point search still checks observed model scores, so the reported best F1/balanced-accuracy/EER points are not limited to the regular grid.

## Interpretation

The important output is the relationship between FAR and FRR, not accuracy alone. A threshold that makes the model call almost everything SPOOF can produce high spoof recall on an imbalanced dataset while producing unacceptable REAL false positives.

Use the Dev report to understand the trade-off first. If the score distributions remain heavily overlapping and no threshold gives a useful balance, the issue is likely in model learning, label/preprocessing alignment, or architecture capacity rather than simply the 0.5 threshold.

Only after the Dev operating point is understood should the selected threshold be evaluated once on the independent Eval split.

## Architecture boundary

The checkpoint is produced by the project's self-contained AASIST-family/AASIST-style model. It is not claimed to be byte-for-byte compatible with the official NAVER/Clova AASIST implementation or its pretrained weights.
