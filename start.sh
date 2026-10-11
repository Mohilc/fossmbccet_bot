#!/usr/bin/env bash
set -e

export PYTHONUNBUFFERED=1

echo "🐧 ==========================================="
echo "🚀 Launching FOSS MBCCET Services on Render"
echo "🐧 ==========================================="

PORT="${PORT:-8000}"
echo "🌐 Starting FastAPI & Telegram Bot on 0.0.0.0:$PORT..."
exec uvicorn app:app --host 0.0.0.0 --port "$PORT"
