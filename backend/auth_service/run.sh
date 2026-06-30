#!/bin/bash
# Run auth-service with shared module accessible
# Works regardless of which directory you call this from

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

export PYTHONPATH="$BACKEND_DIR"
cd "$SCRIPT_DIR"

# Use local venv if present, otherwise try shared auth_service venv
if [ -f "venv/bin/uvicorn" ]; then
    UVICORN="$SCRIPT_DIR/venv/bin/uvicorn"
elif [ -f "../auth_service/venv/bin/uvicorn" ]; then
    UVICORN="$BACKEND_DIR/auth_service/venv/bin/uvicorn"
else
    UVICORN="uvicorn"
fi

echo "Starting auth-service on port 8080 (PYTHONPATH=$BACKEND_DIR)"
exec "$UVICORN" main:app --reload --host 0.0.0.0 --port 8080
