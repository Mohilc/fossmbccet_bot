import os
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database
from ai_analyzer import AIAnalyzer
from config import (
    COMMUNITY_NAME,
    COMMUNITY_GITHUB,
    COMMUNITY_WEBSITE,
    COMMUNITY_TELEGRAM,
    COLLEGE_NAME,
    HOST,
    PORT,
    TELEGRAM_BOT_TOKEN
)

import sys
import time
import subprocess
import threading

# Initialize Database & AI Engine
database.init_db()
ai = AIAnalyzer()

_bot_proc: Optional[subprocess.Popen] = None

def _telegram_bot_supervisor():
    """Background supervisor that ensures telegram_bot.py is always running."""
    global _bot_proc
    while True:
        try:
            print("🚀 [FastAPI] Launching Telegram Bot daemon subprocess...")
            _bot_proc = subprocess.Popen([sys.executable, "telegram_bot.py"])
            _bot_proc.wait()
            print("⚠️ [FastAPI] Telegram Bot daemon exited. Auto-restarting in 2s...")
            time.sleep(2)
        except Exception as e:
            print(f"❌ [FastAPI] Error starting Telegram Bot: {e}")
            time.sleep(5)

app = FastAPI(
    title=f"{COMMUNITY_NAME} - Knowledge & Evaluator API",
    description="Lightweight micro-service & live evaluator portal for FOSS MBCCET Telegram bot",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    if TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != "DUMMY_TOKEN":
        # Launch telegram bot daemon in a dedicated background supervisor thread
        t = threading.Thread(target=_telegram_bot_supervisor, daemon=True, name="TelegramBotSupervisor")
        t.start()
        print("✅ [FastAPI] Telegram Bot supervisor background thread started!")

@app.on_event("shutdown")
def on_shutdown():
    global _bot_proc
    if _bot_proc and _bot_proc.poll() is None:
        try:
            _bot_proc.terminate()
        except Exception:
            pass

# Enable CORS for flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class AskRequest(BaseModel):
    query: str
    student_name: Optional[str] = "Web Explorer"

class ClassifyRequest(BaseModel):
    query: str

# Static Files Directory
STATIC_DIR = Path(__file__).resolve().parent / "static"
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ==================== ENDPOINTS ====================

@app.get("/")
async def serve_dashboard():
    """Serves the rich, lightweight evaluator and community portal."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({
        "community": COMMUNITY_NAME,
        "college": COLLEGE_NAME,
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    })

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    """Lightweight health check for cloud uptime monitoring (Render, Railway, UptimeRobot)."""
    return {
        "status": "healthy",
        "service": "fossmbccet-core",
        "bot_configured": bool(TELEGRAM_BOT_TOKEN),
        "database": "sqlite-ok"
    }

@app.get("/api/stats")
async def get_stats():
    """Returns real-time community learning metrics."""
    stats = database.get_community_stats()
    stats["meta"] = {
        "community_name": COMMUNITY_NAME,
        "college_name": COLLEGE_NAME,
        "github": COMMUNITY_GITHUB,
        "website": COMMUNITY_WEBSITE,
        "telegram": COMMUNITY_TELEGRAM
    }
    return stats

@app.get("/api/queries")
async def get_recent_queries(limit: int = 15):
    """Returns recently resolved student doubts."""
    queries = database.get_recent_queries(limit=limit)
    return {"queries": queries}

@app.post("/api/classify")
async def classify_query(req: ClassifyRequest):
    """Classifies a doubt into FOSS taxonomies and returns structured metadata."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    result = ai.classify_query(req.query.strip())
    return result

@app.post("/api/ask")
async def ask_doubt(req: AskRequest):
    """Interactive endpoint to resolve doubts directly via web evaluator."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    query_text = req.query.strip()
    analysis = ai.analyze_text_query(query_text)

    # Log into database as a web inquiry
    query_id = database.log_query(
        telegram_id=None,
        query_type="text",
        query_text=query_text,
        response_text=analysis.get("direct_answer", ""),
        category=analysis.get("category", "General FOSS"),
        subcategory=analysis.get("subcategory", "General"),
        difficulty=analysis.get("difficulty", "Beginner"),
        tags=analysis.get("tags", [])
    )

    return {
        "query_id": query_id,
        "analysis": analysis
    }

@app.get("/api/resources/{topic}")
async def get_curated_resource(topic: str):
    """Retrieves curated cheat sheets for git, linux, licenses, programs."""
    res = database.get_resource(topic)
    if not res:
        raise HTTPException(status_code=404, detail="Resource topic not found.")
    return res

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Launching {COMMUNITY_NAME} Lightweight Control Center on http://{HOST}:{PORT}")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)
