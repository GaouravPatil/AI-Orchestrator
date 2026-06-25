#!/bin/bash
# Run auth-service with shared module accessible
export PYTHONPATH="$(dirname "$PWD")"
source venv/bin/activate
uvicorn main:app --reload
