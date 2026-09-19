#!/bin/sh
set -eu

MODEL_DIR=${MODEL_DIR:-/tmp/models}
AUDIO_DIR=${AUDIO_STORAGE_PATH:-/tmp/audio}
CHECKPOINT_PATH=${AASIST_CHECKPOINT_PATH:-$MODEL_DIR/best.pt}
PORT_VALUE=${PORT:-10000}

mkdir -p "$MODEL_DIR" "$AUDIO_DIR"

if [ -n "${AASIST_CHECKPOINT_URL:-}" ] && [ ! -f "$CHECKPOINT_PATH" ]; then
  echo "Downloading AASIST checkpoint..."
  curl -fL --retry 3 --retry-delay 2 "$AASIST_CHECKPOINT_URL" -o "$CHECKPOINT_PATH"
fi

if [ ! -f "$CHECKPOINT_PATH" ]; then
  echo "WARNING: AASIST checkpoint is not present. Set AASIST_CHECKPOINT_URL before analysis."
fi

cd /app/backend
alembic upgrade head

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$PORT_VALUE" \
  --workers "${WEB_CONCURRENCY:-1}"
