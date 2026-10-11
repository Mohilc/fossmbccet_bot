#!/usr/bin/env bash
set -e

export PYTHONUNBUFFERED=1

echo "🐧 ==========================================="
echo "🚀 Launching FOSS MBCCET Services on Render"
echo "🐧 ==========================================="

# 1. Start Telegram Bot Daemon in the background with auto-restart supervisor
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "🤖 Starting Telegram Bot Supervisor in background..."
    (
        while true; do
            echo "🚀 Launching telegram_bot.py daemon..."
            python telegram_bot.py || true
            echo "⚠️ Telegram bot process exited. Restarting in 2 seconds..."
            sleep 2
        done
    ) &
    BOT_PID=$!
    echo "✅ Telegram Bot supervisor running (PID: $BOT_PID)"
else
    echo "⚠️ TELEGRAM_BOT_TOKEN is not set. Telegram Bot will not start."
fi

# 2. Start FastAPI Web Evaluator on Render's dynamic PORT in the foreground
PORT="${PORT:-8000}"
echo "🌐 Starting FastAPI Evaluator & Health Portal on 0.0.0.0:$PORT..."
exec uvicorn app:app --host 0.0.0.0 --port "$PORT"
