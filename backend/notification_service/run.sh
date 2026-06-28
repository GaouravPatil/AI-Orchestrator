#!/bin/bash
# Run notification_service
export PYTHONPATH="$(dirname "$PWD")"
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../auth_service/venv" ]; then
    source ../auth_service/venv/bin/activate
fi
uvicorn main:app --reload --port 8004
