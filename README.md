# 🐧 FOSS MBCCET • AI Open Source Mentor & Telegram Bot Daemon

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://python.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Community](https://img.shields.io/badge/FOSS-MBCCET-emerald.svg)](https://github.com/fossmbccet)
[![Framework](https://img.shields.io/badge/Core-FastAPI%20%2B%20PTB%20v20-cyan.svg)](#architecture)

> **Official 24/7 AI Mentor for the FOSS Cell at Mar Baselios Christian College of Engineering & Technology (MBCCET).**  
> Resolves student programming doubts, classifies open-source inquiries, diagnoses terminal & compiler screenshot errors via Multimodal Vision, and teaches Free Software philosophy, Git, Linux, and GSoC pathways.

---

## ⚡ Why Streamlit Was Replaced (The Lean Architecture)

In early prototypes, Streamlit was often used for dashboards. However, for a 24/7 Telegram bot companion, Streamlit introduces heavy overhead:
- ❌ **High Memory Footprint:** Streamlit consumes 200MB–450MB RAM at idle.
- ❌ **Slow Startup Times:** Heavy WebSocket reload cycles delay container cold starts.
- ❌ **Poor Background Daemon Compatibility:** Running a persistent async Telegram bot loop inside Streamlit triggers thread contention and reload instability.

### ✅ What We Built Instead ("Something Less, Far More Capable"):
- **FastAPI Ultra-Lean Engine (~25MB RAM):** Instant sub-second cold starts, zero memory leaks, and native asynchronous concurrency.
- **Dedicated Cloud `/health` Probe:** Ideal for free and production cloud hosts (Render, Railway, Fly.io, UptimeRobot).
- **Embedded Dark-Mode Evaluator Dashboard:** Custom glassmorphic web dashboard with zero framework bloat (vanilla CSS + JS), allowing evaluators and club admins to test doubt resolution, classify inquiries, view live topic distribution bars, and monitor community learning telemetry.
- **Asynchronous Telegram Bot Daemon (`python-telegram-bot` v20+):** Built-in rate limiting, callback query routers, photo/screenshot handling, and interactive inline keyboards.

---

## 📂 Project Architecture

```
fossmbccet/
├── app.py                      # FastAPI Evaluator Control Center & Live Telemetry API
├── telegram_bot.py             # 24/7 Telegram Bot Daemon (Text Q&A, Photo Diagnostics)
├── ai_analyzer.py              # Multi-Engine AI Ensemble (DiffusionGemma, Muse Glimmer, Nemotron, Laguna, Kimi)
├── prompts.py                  # System instructions, classification taxonomies & schemas
├── database.py                 # SQLite persistence layer with migrations & telemetry
├── report_generator.py         # Telegram HTML message formatter & ReportLab PDF generator
├── config.py                   # Centralized configuration & environment loader
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Lightweight container definition
├── docker-compose.yml          # Multi-container orchestration (Web Portal + Telegram Daemon)
├── README.md                   # Complete documentation & deployment guide
├── .gitignore                  # Git protection rules (.env, *.db, cache)
├── .env.example                # Configuration template
│
├── data/
│   ├── fossmbccet.db           # SQLite database (auto-created on startup)
│   └── uploads/                # Cached screenshots & generated PDF reports
│
├── static/                     # Embedded sleek dark-mode FOSS dashboard
│   ├── index.html              # Cyberpunk/FOSS terminal dashboard UI
│   ├── style.css               # Rich glassmorphic CSS styling
│   └── app.js                  # Dynamic client telemetry & interactive solver
│
└── tests/
    └── test_end_to_end.py      # Automated tests for AI engine, DB, API & Bot handlers
```

---

## 🧠 Multi-Model AI Ensemble (NVIDIA NIM + Multimodal Vision)

The bot harnesses a multi-engine cascade so students always receive the fastest and highest quality response:

| Model | Provider / Architecture | Primary Role |
| :--- | :--- | :--- |
| **`google/diffusiongemma-26b-a4b-it`** | NVIDIA NIM / Google | ⚡ **Ultra-Fast Visual OCR & Terminal Screenshot Diagnostic (~1.0s)** |
| **`meta/muse-glimmer-30b`** | NVIDIA NIM / Meta | 🌿 **High-Speed FOSS Concept & Question Resolution** |
| **`nvidia/nemotron-3.5-lightning-30b-a3b`** | NVIDIA NIM / NVIDIA | 🧠 **Deep Reasoning, Linux SysAdmin & Complex Bug Diagnosis** |
| **`poolside/laguna-xs-2.1`** | NVIDIA NIM / Poolside | 💻 **Developer Code & Software Logic Analysis** |
| **`moonshotai/kimi-k3`** | NVIDIA NIM / Moonshot AI | 🔍 **Long-Context Deep Reasoning & Vision Fallback** |
| **`gemini-1.5-flash`** | Google AI Studio | ☁️ **Secondary Cloud Engine** |
| **Pedagogical Heuristics Engine** | Local Python Engine | 🛡️ **Zero-Downtime Offline Fallback** |

---

## 🌟 Key Capabilities

### 1. 🎓 FOSS Teaching & Pedagogical Reasoning
- **Git & Version Control:** Branch workflows, merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`), interactive rebasing, conventional commits.
- **Linux System Administration:** File permissions (`chmod 755` vs `644`), systemd service management, bash scripting, UNIX pipes.
- **Open Source Licensing & Ethics:** Clear distinction between Permissive (MIT, Apache 2.0, BSD) and Copyleft (GNU GPLv3, AGPLv3).
- **Mentorship Programs:** Guidance for Google Summer of Code (GSoC), Hacktoberfest, Outreachy, and finding "Good First Issues".
- **FOSS Alternatives:** Replaces proprietary recommendations with open-source equivalents (e.g. GIMP, Inkscape, LibreOffice, VSCodium).

### 2. 📸 Multimodal Screenshot & Code Diagnostics
Students can take a photo or screenshot of their computer screen showing a terminal error, gcc compiler bug, or Git conflict. Tuxie inspects the image, extracts the stack trace, and sends copy-pasteable terminal commands to fix it.

### 3. 🏷️ Automated Topic Classification
Classifies every inquiry into standard taxonomies:
- Category & Subcategory
- Difficulty Level (`Beginner`, `Intermediate`, `Advanced`)
- Keyword Tags (`#git`, `#linux`, `#licensing`, etc.)
- Recommended FOSS ecosystem tools

### 4. 📄 PDF Diagnostic Report Generator
Students can click the **"Download PDF Report"** button in Telegram to receive a clean, professionally formatted ReportLab PDF reference card summarizing the resolution.

---

## 🚀 Quickstart Guide

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/fossmbccet/bot.git
cd fossmbccet

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# 1. Obtain via Telegram @BotFather:
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ

# 2. Obtain free Gemini key via https://aistudio.google.com/
GEMINI_API_KEY=AIzaSy...

# 3. Community Meta (defaults already configured)
COMMUNITY_NAME=FOSS MBCCET
COLLEGE_NAME=Mar Baselios Christian College of Engineering and Technology (MBCCET)
```

> **Note:** If `GEMINI_API_KEY` is omitted during local development, the built-in **Offline Heuristic Engine** activates automatically, ensuring full functionality for common Git, Linux, and licensing queries!

---

## 🏃 Running the Services

### Option A: Run Both via Docker Compose (Recommended)

```bash
docker-compose up --build -d
```
- Web Evaluator & Health API: `http://localhost:8000`
- Telegram Bot Daemon: Active 24/7 in background
- Persistent Database: Mapped to `./data`

### Option B: Run Locally

In Terminal 1 (Web Evaluator Dashboard & API):
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

In Terminal 2 (Telegram Bot Daemon):
```bash
python telegram_bot.py
```

---

## 🤖 Telegram Bot Commands

| Command | Description |
| :--- | :--- |
| `/start` | Welcome screen & interactive quick-action keyboard |
| `/ask <query>` | Ask any coding, Linux, or open source doubt |
| `/classify <topic>` | Classify an inquiry into FOSS taxonomies |
| `/git` | Curated Git workflow and branching cheat sheet |
| `/linux` | Linux CLI essentials & permissions quick reference |
| `/licenses` | Permissive vs Copyleft open source license guide |
| `/programs` | Roadmap for GSoC, Hacktoberfest & Outreachy |
| `/stats` | Live community metrics (students helped, top topics) |
| `/community` | FOSS MBCCET club links, GitHub & events |
| `/help` | Complete bot manual |

> 💡 **Natural Chat:** Students can simply send text or photos without any command prefix!

---

## 🧪 Running Automated Tests

Run the full end-to-end verification test suite:

```bash
pytest tests/test_end_to_end.py -v
```

This validates:
- SQLite schema migrations, user tracking & telemetry
- AI reasoning engine & classification accuracy across all domains
- Telegram HTML escaping & PDF report generation
- FastAPI endpoints (`/health`, `/api/stats`, `/api/classify`, `/api/ask`)
- Telegram bot handler registration

---

## 🌐 Cloud Deployment Options

### Render / Railway / Koyeb
1. Connect your GitHub repository.
2. Set Environment Variables: `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`.
3. Set Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Health check path: `/health`

### Linux VPS / Self-Hosting
Use `systemd` or `docker-compose`:
```bash
docker compose up -d
```

---

## 📜 License & Community

Distributed under the **GNU General Public License v3.0 (GPLv3)**.  
Maintained with passion by the **FOSS MBCCET** Core Team.
