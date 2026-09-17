# Phase 05 — AASIST Training Engine

## Purpose

This layer trains the self-contained AASIST-family detector added in Phase 05. It consumes the existing ASVspoof 2019 LA PyTorch Dataset/DataLoader and model-input preprocessor without moving dataset-specific logic into the model or trainer.

## Pipeline

```text
ASVspoof protocol
    -> ASVspoofTorchDataset
    -> DataLoader + collate
    -> AudioModelInputPreprocessor
    -> AASISTModel
    -> weighted CrossEntropyLoss
    -> backward / gradient clipping
    -> AdamW
    -> cosine LR scheduler
    -> dev validation
    -> best/latest checkpoints
```

## Training behavior

- Project labels remain `REAL=0`, `SPOOF=1`.
- Train-class counts are read from the validated protocol layer and converted to inverse-frequency class weights.
- Default target length is 4 seconds at 16 kHz (64,000 samples).
- Default batch size is 2 to remain practical for the RTX 3050 4 GB GPU.
- CUDA uses mixed precision by default; CPU automatically runs without CUDA AMP.
- Gradient accumulation is configurable for effective larger batch sizes.
- Gradients are clipped to a maximum norm of 5.0.
- AdamW and cosine annealing are used for the optimizer/scheduler.
- Validation reports loss, accuracy, precision, recall, F1, ROC-AUC, and EER when both classes are present.
- Best checkpoint is selected by development F1.
- Checkpoints are written atomically and contain model, optimizer, scheduler, scaler, configuration, and epoch metrics.
- `history.json` records epoch-level training and development metrics.

## Smoke test before real training

From the project root after pulling the branch:

```powershell
cd E:\projects\AI-Powered-Voice-Cloning-Detection-Prevention-System
cd backend
python -m pytest tests/test_aasist_training.py -v
python scripts/train_aasist.py --epochs 1 --batch-size 2 --max-train-batches 2 --max-dev-batches 1
```

The second command intentionally trains only a few batches. It validates the complete real-data path before a long run.

## Full training

After the smoke test is successful:

```powershell
python scripts/train_aasist.py --epochs 10 --batch-size 2 --gradient-accumulation-steps 2
```

For a longer run, increase epochs only after reviewing development F1, ROC-AUC, and EER.

## Checkpoints

Default directory:

```text
backend/artifacts/checkpoints/aasist/
```

Files:

- `best.pt` — best development F1 checkpoint.
- `latest.pt` — latest resumable checkpoint.
- `history.json` — epoch history.

Resume example:

```powershell
python scripts/train_aasist.py --epochs 20 --resume artifacts/checkpoints/aasist/latest.pt
```

## Important architecture note

The model in this project is an AASIST-family/AASIST-style self-contained implementation. It is intentionally not claimed to be byte-for-byte compatible with the official NAVER AASIST implementation or its pretrained checkpoints. Training in this phase therefore means training the project's own detector weights from scratch.
