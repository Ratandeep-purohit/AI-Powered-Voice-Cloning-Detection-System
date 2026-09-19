#!/bin/sh
set -eu
mkdir -p /data/audio /data/models
CHECKPOINT_PATH=$AASIST_CHECKPOINT_PATH
if [ -n "$AASIST_CHECKPOINT_URL" ] && [ ! -f "$CHECKPOINT_PATH" ]; then
  echo "Downloading AASIST checkpoint..."
  curl -fL --retry 3 --retry-delay 2 "$AASIST_CHECKPOINT_URL" -o "$CHECKPOINT_PATH"
fi
if [ ! -f "$CHECKPOINT_PATH" ]; then
  echo "WARNING: AASIST checkpoint is not present. Set AASIST_CHECKPOINT_URL or provide AASIST_CHECKPOINT_PATH before analysis."
fi
cd /app/backend
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cleanup() { kill "$BACKEND_PID" 2>/dev/null || true; }
trap cleanup INT TERM EXIT
nginx -g 'daemon off;'
