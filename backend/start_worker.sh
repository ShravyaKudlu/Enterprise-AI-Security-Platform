#!/bin/bash
# Start RQ worker with correct Python path

cd /home/shravyashanbhogue/prod/coolStufs/faysal/backend
export PYTHONPATH=/home/shravyashanbhogue/prod/coolStufs/faysal/backend:$PYTHONPATH
./venv/bin/rq worker --url redis://localhost:6379/0