#!/bin/bash
set -e

# Run ai-service with shared and ai-service modules accessible
export PYTHONPATH="$(dirname "$PWD")"

# Use auth_service venv (shared) or local venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../auth_service/venv" ]; then
    source ../auth_service/venv/bin/activate
fi

uvicorn main:app --reload --port 8002
