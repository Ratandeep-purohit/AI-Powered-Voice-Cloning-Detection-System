# Phase 05 — ASVspoof 2019 LA Dataset Protocol + PyTorch Dataset Layer

## Scope

This phase starts the ML/data layer by adding configuration, deterministic ASVspoof 2019 Logical Access (LA) CM protocol parsing, audio-path resolution, dataset integrity validation, and a PyTorch Dataset/DataLoader boundary.

The large ASVspoof dataset remains external to the repository. No dataset audio or protocol corpus is committed here.

## Local dataset layout

Expected local root:

```text
E:\DataSet\LA\
├── ASVspoof2019_LA_cm_protocols\
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
bonafide → REAL (0)
spoof    → SPOOF (1)
```

## Dataset integrity

Before model training, the validator checks every expected protocol entry against the corresponding FLAC file and detects duplicate audio IDs.

The verified local dataset currently reports:

| Split | Total | REAL | SPOOF | Missing | Duplicates |
|---|---:|---:|---:|---:|---:|
| Train | 25,380 | 2,580 | 22,800 | 0 | 0 |
| Dev | 24,844 | 2,548 | 22,296 | 0 | 0 |
| Eval | 71,237 | 7,355 | 63,882 | 0 | 0 |

Overall integrity validation passed.

## PyTorch dataset layer

`ASVspoofTorchDataset` resolves protocol entries and loads FLAC audio as float tensors.

The Dataset boundary currently:

- maps `REAL` to `0` and `SPOOF` to `1`;
- converts multi-channel audio to mono;
- resamples audio to the configured target sample rate (default 16 kHz);
- returns waveform tensors shaped `[1, time]`;
- preserves split, speaker ID, audio ID, and source path metadata;
- does not perform model-specific feature extraction.

`asvspoof_collate_fn` batches variable-length waveforms by zero-padding to the longest sample and returns an `attention_mask` identifying valid waveform samples.

## Design boundary

The current dataset layer does not yet:

- crop or pad to a model-specific fixed duration;
- extract spectrograms or other model-specific features;
- train a model;
- run inference;
- calculate evaluation metrics.

Keeping these responsibilities separate avoids locking the dataset loader to a particular detector architecture too early.

## Validation

The Phase 05 test suite covers:

- protocol parsing;
- dataset audio-path resolution;
- dataset integrity checks;
- waveform loading;
- REAL/SPOOF label mapping;
- mono conversion;
- resampling;
- variable-length DataLoader collation;
- invalid sample-rate and split handling.
