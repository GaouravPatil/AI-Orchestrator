#!/bin/bash
export PYTHONPATH="$(dirname "$PWD")"
source ../auth_service/venv/bin/activate
uvicorn main:app --reload --port 8002
