#!/bin/bash
# Run k8s_service with shared and k8s_service modules accessible
export PYTHONPATH="$(dirname "$PWD")"
# Use the auth_service venv if k8s doesn't have its own, or activate local one if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../auth_service/venv" ]; then
    source ../auth_service/venv/bin/activate
fi
uvicorn main:app --reload --port 8001
