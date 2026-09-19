# Hugging Face Spaces Deployment

This project is packaged as a Docker Space. Hugging Face Docker Spaces expose the application on port 7860; Nginx serves the React build and proxies /api/* to FastAPI.

## Required Space configuration

Create a new Hugging Face Space with Docker as the SDK.

Set these runtime secrets/variables in Space Settings:
- DATABASE_URL — external PostgreSQL connection string.
- JWT_SECRET — strong random signing secret.
- AASIST_CHECKPOINT_URL — authorized best.pt checkpoint URL, if the checkpoint is not baked into the image.

Recommended variables:
- APP_ENV=production
- AASIST_CHECKPOINT_PATH=/data/models/best.pt
- AUDIO_STORAGE_PATH=/data/audio
- AASIST_DETECTION_THRESHOLD=0.5977
- CORS_ALLOWED_ORIGINS= (empty when frontend and API share the same Space origin)

Use Secrets for database credentials, JWT secrets, and private model URLs/tokens.

## Database

Use an external PostgreSQL service. The startup script runs Alembic migrations before starting the application.

## AASIST checkpoint

The production checkpoint is intentionally external to Git. Before real analysis, either provide AASIST_CHECKPOINT_URL or adapt this deployment to a Hugging Face model repository and preload the checkpoint.

The container can boot without the checkpoint, but analysis requires it.

## Local Docker smoke test

From the repository root:

```powershell
docker build -t voiceguard-space .
docker run --rm -p 7860:7860 --env-file .env voiceguard-space
```

Then open http://localhost:7860.

The container needs a reachable PostgreSQL database and valid AASIST checkpoint before authenticated analysis can complete.
