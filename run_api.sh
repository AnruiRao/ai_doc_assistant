#!/bin/bash
cd "$(dirname "$0")"
export $(grep -v '^#' .env | xargs)
uv run uvicorn api.main:app --reload --port 8000 --app-dir src
