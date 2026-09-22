#!/usr/bin/env bash
# Runs the mock Smart Home API (:9000) and the agent API (:8000) together.
set -e

echo "Starting mock Smart Home API on :9000"
uvicorn mock_api.main:app --port 9000 --reload &
MOCK_PID=$!

echo "Starting agent API on :8000"
uvicorn api.main:app --port 8000 --reload &
API_PID=$!

trap "kill $MOCK_PID $API_PID" EXIT
wait
