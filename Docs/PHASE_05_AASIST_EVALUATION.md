# Phase 05 — AASIST Evaluation

## Purpose

This stage evaluates the trained project AASIST-family detector against the unseen ASVspoof 2019 LA `eval` split.

The evaluation path intentionally reuses the same dataset loader and deterministic 16 kHz / mono / fixed-duration preprocessing used during training. The dataset and model checkpoints remain external runtime artifacts and are not committed to the repository.

## Metrics

The report contains:

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC using the SPOOF probability as the positive score
- EER (Equal Error Rate) from a threshold sweep
- Confusion matrix counts: TN, FP, FN, TP
- Evaluation loss and sample count

Accuracy is retained for context, but the primary detector metrics are F1, ROC-AUC, EER, and the confusion matrix because the ASVspoof split is strongly imbalanced.

## Checkpoint

Use the best validation checkpoint produced by training:

```text
artifacts/checkpoints/aasist/best.pt
```

The evaluator expects the checkpoint to contain `model_state_dict`, matching the project `AASISTModel` architecture.

## Run full evaluation

From `backend/`:

```powershell
python scripts/evaluate_aasist.py --dataset-root "E:\DataSet\LA" --checkpoint "artifacts\checkpoints\aasist\best.pt" --batch-size 2 --device cuda
```

The JSON report is written to:

```text
backend/artifacts/evaluation/aasist/eval.json
```

Runtime-generated artifacts under `backend/artifacts/` are ignored by Git.

## Quick smoke evaluation

For a fast pipeline check, temporarily use a small batch size and a tiny evaluation subset only after extending the CLI with a bounded-evaluation option. The normal evaluation command intentionally processes the complete Eval split so the reported metrics represent the full protocol.

## Interpretation

A single Dev F1 value does not establish generalization. The full Eval split is the next independent measurement. Compare Precision, Recall, F1, ROC-AUC, EER and the confusion matrix together, and keep the checkpoint identity with the report for reproducibility.

The project model is an AASIST-family implementation created in this repository. It is not claimed to be byte-for-byte compatible with the official NAVER/Clova AASIST implementation or its pretrained weights.
