# Phase 05 — ASVspoof 2019 LA Dataset Protocol Layer

## Scope

This phase starts the ML/data layer by adding configuration and a deterministic parser for the ASVspoof 2019 Logical Access (LA) CM protocol files.

The large ASVspoof dataset remains external to the repository. No dataset audio or protocol corpus is committed here.

## Local dataset layout

Expected local root:

```text
E:\DataSet\LA\
├── ASVspoof2019_LA_asv_protocols\
├── ASVspoof2019_LA_train\
├── ASVspoof2019_LA_dev\
├── ASVspoof2019_LA_eval\
└── ...
```

Set:

```text
ASVSPOOF_DATASET_ROOT=E:\DataSet\LA
```

## Protocol files

The parser currently supports:

- `train` → `ASVspoof2019.LA.cm.train.trn.txt`
- `dev` → `ASVspoof2019.LA.cm.dev.trl.txt`
- `eval` → `ASVspoof2019.LA.cm.eval.trl.txt`

A CM row is expected to contain five whitespace-separated fields:

```text
speaker_id audio_id attack_system attack_version label
```

The parser maps:

```text
bonafide → REAL
spoof    → SPOOF
```

## Design boundary

The protocol layer only resolves dataset metadata and labels. It does not yet:

- load audio into tensors;
- perform feature extraction;
- train a model;
- run inference;
- calculate evaluation metrics.

Those responsibilities are introduced in subsequent Phase 05 steps.

## Validation

`backend/tests/test_asvspoof.py` verifies:

- label mapping;
- train/dev/eval protocol resolution;
- missing protocol rejection;
- malformed row rejection;
- unknown-label rejection;
- blank/comment handling.
