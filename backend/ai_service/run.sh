#!/bin/bash
# Run ai-service with shared module accessible
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
export PYTHONPATH="$BACKEND_DIR"
cd "$SCRIPT_DIR"
[ -f "venv/bin/uvicorn" ] && UVICORN="$SCRIPT_DIR/venv/bin/uvicorn" \
  || UVICORN="$BACKEND_DIR/auth_service/venv/bin/uvicorn"
echo "Starting ai-service on port 8002"
exec "$UVICORN" main:app --reload --host 0.0.0.0 --port 8002
