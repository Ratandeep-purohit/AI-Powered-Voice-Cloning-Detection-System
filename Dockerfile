# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend-build
WORKDIR /src/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 APP_ENV=production APP_HOST=127.0.0.1 APP_PORT=8000 AASIST_CHECKPOINT_PATH=/data/models/best.pt AUDIO_STORAGE_PATH=/data/audio
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg nginx ca-certificates curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --upgrade pip && python -m pip install --extra-index-url https://download.pytorch.org/whl/cu130 -r /app/backend/requirements.txt
COPY backend/ /app/backend/
COPY --from=frontend-build /src/frontend/dist/ /usr/share/nginx/html/
COPY deployment/nginx.conf /etc/nginx/nginx.conf
COPY deployment/start.sh /app/deployment/start.sh
RUN useradd --create-home --uid 1000 --shell /bin/bash appuser && mkdir -p /data/audio /data/models /var/cache/nginx /var/log/nginx /run/nginx && chown -R appuser:appuser /app /data /usr/share/nginx/html /var/cache/nginx /var/log/nginx /run/nginx
USER appuser
EXPOSE 7860
ENTRYPOINT ["/app/deployment/start.sh"]
