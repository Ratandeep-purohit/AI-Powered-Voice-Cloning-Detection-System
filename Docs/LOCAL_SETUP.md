# Local Development Setup

Phase 00 provides the runnable FastAPI + React/Vite foundation and PostgreSQL connectivity configuration. Authentication, business models, audio processing, AI detection, risk, policy, alerts, WebSockets, and Copilot are intentionally not included yet.

## Prerequisites

- Python 3.11+
- Node.js 20+
- npm
- PostgreSQL 15+ or Docker Desktop
- Git

## 1. Clone and configure

```bash
git clone <repository-url>
cd AI-Powered-Voice-Cloning-Detection-System
cp .env.example .env
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Keep `.env` local and never commit it.

## 2. Start PostgreSQL with Docker

```bash
docker compose up -d postgres
```

The default local database is `voice_cloning_detection` on port `5432`.

## 3. Backend

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API from the `backend` directory:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify:

```text
GET http://127.0.0.1:8000/api/v1/health
```

When PostgreSQL is reachable, the response reports `healthy` and `database: connected`. Otherwise the endpoint returns HTTP 503 with a safe `degraded` response.

Run backend tests:

```bash
pytest
```

## 4. Frontend

From the repository root:

```bash
cd frontend
npm install
npm run dev
```

The frontend reads `VITE_API_BASE_URL` from its environment. Copy `frontend/.env.example` to `frontend/.env` if a different API address is required.

Build:

```bash
npm run build
```

Test:

```bash
npm run test
```

## Security notes

- `.env` and generated artifacts are ignored by Git.
- `.env.example` contains placeholders/default local development values only.
- No authentication or authorization is implemented in Phase 00.
- No business database tables are created in Phase 00.
- The health endpoint never returns database credentials or connection details.
