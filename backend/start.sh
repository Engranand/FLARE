#!/usr/bin/env bash
set -e

# ==============================================================================
# FLARE Backend Render Startup Entrypoint
# ==============================================================================

# 1. Normalize Render DATABASE_URL scheme to explicit psycopg3 driver format
# Render injects postgresql:// or postgres://; FLARE enforces postgresql+psycopg://
if [ -n "$DATABASE_URL" ]; then
  export DATABASE_URL=$(echo "$DATABASE_URL" | sed -E 's/^postgres(ql)?:\/\//postgresql+psycopg:\/\//')
  echo "[FLARE STARTUP] Normalized DATABASE_URL driver to postgresql+psycopg"
fi

# 2. Run Alembic database migrations to head revision if DATABASE_URL is configured
if [ -n "$DATABASE_URL" ]; then
  echo "[FLARE STARTUP] Applying Alembic database migrations (upgrade head)..."
  alembic upgrade head
  echo "[FLARE STARTUP] Database migrations applied successfully."
fi

# 3. Launch FastAPI server via Uvicorn
PORT="${PORT:-8000}"
echo "[FLARE STARTUP] Starting Uvicorn on 0.0.0.0:${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
