#!/usr/bin/env bash
set -e

echo "🐧 ==========================================="
echo "🚀 Launching FOSS MBCCET Services on Render"
echo "🐧 ==========================================="

# 1. Start Telegram Bot Daemon in the background
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "🤖 Starting Telegram Bot Daemon in background..."
    python telegram_bot.py &
    BOT_PID=$!
    echo "✅ Telegram Bot daemon running (PID: $BOT_PID)"
else
    echo "⚠️ TELEGRAM_BOT_TOKEN is not set. Telegram Bot will not start."
fi

# 2. Start FastAPI Web Evaluator on Render's dynamic PORT in the foreground
PORT="${PORT:-8000}"
echo "🌐 Starting FastAPI Evaluator & Health Portal on 0.0.0.0:$PORT..."
exec uvicorn app:app --host 0.0.0.0 --port "$PORT"
