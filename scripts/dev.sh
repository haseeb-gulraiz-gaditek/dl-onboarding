#!/usr/bin/env bash
# Mesh dev — runs FastAPI (8000) + Next.js (3000) concurrently.
# Per spec-delta frontend-core F-FE-10.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Activate venv if present.
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

cleanup() {
  echo
  echo "[dev] shutting down…"
  kill 0 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[dev] starting FastAPI on :8000"
python -m uvicorn app.main:app --reload --port 8000 &

echo "[dev] starting Next.js on :3000"
(cd frontend && npm run dev) &

wait
