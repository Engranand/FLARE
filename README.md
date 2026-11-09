# FLARE

Scientific Intelligence Platform for Spacecraft Fire Safety.

FLARE is a research workspace intended to help researchers explore microgravity combustion experiments, compare conditions, inspect evidence and identify research gaps. It is not a generic chatbot.

## Context and current scope

The project brief targets the NASA Space Apps Challenge 2026 challenge **“Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data.”** This wording and association come from the project brief and are not independently verified here.

Milestone 1 delivers a React dashboard, FastAPI service, environment configuration, connectivity states and automated tests. **Scientific data ingestion is not implemented. No NASA experimental data has been downloaded or validated.** No experiments, measurements, findings, predictions, charts or statistics are fabricated. No database, RAG, LLM agents or analytics are implemented.

Initial target: NASA BASS-II, PSI-25, DOI `10.60555/4qc4-de67`. See [research sources](docs/research_sources.md) for provenance limits.

## Stack

Frontend: React, Vite, TypeScript, Tailwind CSS, React Router, Lucide React, Vitest.
Backend: Python 3.12+, FastAPI, Uvicorn, Pydantic, Pydantic Settings, Pytest, HTTPX.
Use Node.js 22.12+ (an active LTS release is recommended) and npm.

## Repository

```text
frontend/src/
  components/ layouts/ pages/ services/ hooks/ types/ utils/
backend/app/
  api/ core/ schemas/
  models/ services/ ingestion/ analytics/ evidence/ rag/
backend/tests/
data/raw/bass_ii/       # reserved, no source data
data/processed/       # reserved, no normalized data
data/manifests/       # reserved for provenance manifests
docs/                  # architecture, proposed schema, research sources
```

Reserved module directories contain scope notes; they are not implemented services.

## Local setup (PowerShell)

Run from the repository root. Use a stable Python release (not an alpha). On this machine, the working interpreter is `C:\Users\anand\AppData\Local\Programs\Python\Python312\python.exe`; the default `python` points to an incompatible 3.14 alpha. The existing backend virtual environment was created with Python 3.12.8. Create local environment files once; do not overwrite existing configuration.

```powershell
cd backend
# Use your stable Python 3.12+ executable here.
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal from the root:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

Open http://localhost:5173. API docs: http://localhost:8000/docs.
On macOS/Linux, use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe` and `cp` instead of `Copy-Item`.

Frontend routes: `/`, `/experiments`, `/compare`, `/evidence`, `/research-gaps`, `/settings`. Unknown routes show a recovery link. Production static hosting must rewrite frontend paths to `index.html`.

## Configuration

Backend loads `backend/.env`; process environment overrides it.

| Variable | Default | Meaning |
| --- | --- | --- |
| APP_NAME | FLARE Scientific Intelligence API | API title and response name |
| APP_VERSION | 0.1.0 | Application/API version |
| ENVIRONMENT | development | Safe deployment label |
| API_V1_PREFIX | /api/v1 | Router prefix, no trailing slash |
| FRONTEND_ORIGIN | http://localhost:5173 | One exact allowed browser origin, no trailing slash |
| VITE_API_BASE_URL | http://localhost:8000/api/v1 | Public frontend API base, including prefix |

Restart the relevant server after changes. Vite variables are public and embedded at build time; never put credentials there. If using a different frontend host/port, update `FRONTEND_ORIGIN`. If changing the backend prefix, also update `VITE_API_BASE_URL`. Only allowlisted system fields are returned by the API.

`GET /` returns application name, version and documentation path. `GET /api/v1/health` returns `status`, `application_name`, `version`. `GET /api/v1/system/info` returns `application_name`, `api_version`, `environment`. Health is process availability only; it does not imply dataset readiness.

The dashboard checks health on mount and on manual retry, with an eight-second timeout. It displays Checking, Connected or Disconnected. Connection failure does not hide the workspace.

## Checks

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

```powershell
cd frontend
npm test
npm run typecheck
npm run build
```

Tests use in-process HTTP or mocked fetch and require no external APIs or credentials. Frontend dependencies are locked in `package-lock.json`. Backend direct requirements have compatibility bounds; `requirements.lock.txt` records the verified environment for reproducible installation (`pip install -r requirements.lock.txt`).

Docker Compose is intentionally deferred: Docker is unavailable in the implementation environment, so reliable container startup could not be verified. Both services run independently using the commands above.

## Next milestone

**Milestone 2: BASS-II source audit and provenance-first ingestion.** Verify official metadata, access terms, actual archive structure, units and missing-value conventions; then implement a small deterministic ingestion pipeline with source hashes, manifests, schema validation, rejection reporting and fixture-based tests. Revise the proposed dictionary against real source files before loading experimental records. Do not add scientific inference or RAG in that milestone.

Actual execution results and environment limitations: [verification report](docs/verification.md).
