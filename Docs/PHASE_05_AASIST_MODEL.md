# Phase 05 — AASIST Model Integration

## Scope

This step adds the detector-model boundary after the ASVspoof Dataset/DataLoader and deterministic model-input preprocessing layers.

Pipeline:

```text
ASVspoof Dataset/DataLoader
        ↓
Model Input Preprocessor
        ↓
AASISTModel
        ↓
[REAL, SPOOF] logits
        ↓
softmax probabilities / predicted label
```

## Model contract

`backend/app/services/aasist_model.py` exposes:

- `AASISTModelConfig`
- `AASISTModel`
- `AASISTModel.probabilities(logits)`
- `AASISTModel.predict_label(logits)`

Input:

```text
[batch, 1, time]
```

at 16 kHz by default.

Output:

```text
[batch, 2]
```

Class convention:

```text
0 = REAL
1 = SPOOF
```

## Architecture boundary

The implementation follows the core ideas of AASIST — raw-audio Sinc-style filtering, spectro-temporal residual encoding, graph attention over compact nodes, and attention-weighted graph pooling.

This repository implementation is intentionally self-contained and does **not** claim byte-for-byte checkpoint compatibility with the official NAVER implementation. The official reference is `clovaai/aasist`.

No pretrained weights are committed in this step.

## Validation

`backend/tests/test_aasist_model.py` validates:

- forward output shape;
- finite logits;
- probability normalization;
- REAL/SPOOF label mapping;
- backward/gradient flow;
- invalid input rejection;
- NaN/Inf rejection;
- CUDA forward pass when CUDA is available.

## Training boundary

This step does not train the model. Training comes after the forward-pass contract is verified. The next ML step is the training loop with class-imbalance handling and validation metrics such as F1, ROC-AUC, EER, and confusion matrix.
