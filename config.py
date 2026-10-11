import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")

# Bot & Service Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "fossmbccet-admin-key")

# NVIDIA NIM Multi-Model Pool
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

# Vision Models
NVIDIA_VISION_KEY = os.getenv("NVIDIA_VISION_KEY", "")
NVIDIA_VISION_MODEL = os.getenv("NVIDIA_VISION_MODEL", "google/diffusiongemma-26b-a4b-it")

# Text & Reasoning Models
NVIDIA_NEMOTRON_KEY = os.getenv("NVIDIA_NEMOTRON_KEY", "")
NVIDIA_NEMOTRON_MODEL = os.getenv("NVIDIA_NEMOTRON_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")

NVIDIA_MUSE_KEY = os.getenv("NVIDIA_MUSE_KEY", "")
NVIDIA_MUSE_MODEL = os.getenv("NVIDIA_MUSE_MODEL", "meta/muse-glimmer-30b")

NVIDIA_LAGUNA_KEY = os.getenv("NVIDIA_LAGUNA_KEY", "")
NVIDIA_LAGUNA_MODEL = os.getenv("NVIDIA_LAGUNA_MODEL", "poolside/laguna-xs-2.1")

NVIDIA_KIMI_KEY = os.getenv("NVIDIA_KIMI_KEY", "")
NVIDIA_KIMI_MODEL = os.getenv("NVIDIA_KIMI_MODEL", "moonshotai/kimi-k3")

# Community Meta
COMMUNITY_NAME = os.getenv("COMMUNITY_NAME", "FOSS MBCCET")
COMMUNITY_GITHUB = os.getenv("COMMUNITY_GITHUB", "https://github.com/fossmbccet")
COMMUNITY_WEBSITE = os.getenv("COMMUNITY_WEBSITE", "https://fossmbccet.org")
COMMUNITY_TELEGRAM = os.getenv("COMMUNITY_TELEGRAM", "https://t.me/fossmbccet")
COLLEGE_NAME = os.getenv("COLLEGE_NAME", "Mar Baselios Christian College of Engineering and Technology (MBCCET)")

# Server Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Paths
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
DATABASE_PATH = DATA_DIR / "fossmbccet.db"

# Create directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
