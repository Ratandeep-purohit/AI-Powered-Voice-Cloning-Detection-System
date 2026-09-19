# Render Backend Deployment

This deployment runs only the FastAPI backend on Render. The React frontend is deployed separately on Vercel.

## Render service settings

- Service type: Web Service
- Language: Docker
- Branch: main
- Dockerfile path: `Dockerfile.render`
- Health check path: `/api/v1/health/live`
- Plan: Free for the initial demo deployment

The container binds FastAPI to Render's `PORT` on `0.0.0.0`.

## Required environment variables

Set these in Render's Environment tab. Do not commit secret values.

```text
APP_ENV=production
LOG_LEVEL=INFO
APP_HOST=0.0.0.0
APP_PORT=10000
DATABASE_URL=<Supabase PostgreSQL URI>
JWT_SECRET=<long random secret>
AUDIO_STORAGE_PATH=/tmp/audio
AASIST_CHECKPOINT_PATH=/tmp/models/best.pt
AASIST_CHECKPOINT_URL=<public HTTPS URL to best.pt>
CORS_ALLOWED_ORIGINS=<Vercel frontend origin>
```

For the first backend boot test, `AASIST_CHECKPOINT_URL` may be omitted. The health endpoint does not require the model checkpoint, but analysis does.

## Notes

- Render Free has an ephemeral filesystem. Uploaded audio and downloaded checkpoints are not durable across restarts/redeploys.
- The backend uses a CPU-only PyTorch wheel for this service. Local CUDA requirements remain unchanged.
- Free Render compute has limited CPU/RAM, so AASIST inference may be slow or may require a larger plan if the model exceeds the free memory limit.
- Supabase remains the durable PostgreSQL database.
