import os
import sys
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database
from ai_analyzer import AIAnalyzer
from report_generator import format_telegram_response, generate_pdf_report
from app import app
from fastapi.testclient import TestClient
from telegram_bot import build_bot_application

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database schema is created before tests."""
    database.init_db()

# ==================== 1. DATABASE TESTS ====================

def test_database_initialization():
    """Verifies SQLite tables and seeded resources exist."""
    git_res = database.get_resource("git")
    assert git_res is not None
    assert "Git" in git_res["title"]
    assert "rebase" in git_res["content"].lower() or "clone" in git_res["content"].lower()

    linux_res = database.get_resource("linux")
    assert linux_res is not None
    assert "apt" in linux_res["content"].lower()

def test_database_user_and_query_logging():
    """Tests user registration, query logging, and community analytics."""
    test_id = 999888777
    database.register_or_update_user(
        telegram_id=test_id,
        username="hacker_tux",
        first_name="Tux",
        last_name="Torvalds"
    )

    query_id = database.log_query(
        telegram_id=test_id,
        query_type="text",
        query_text="How to fix git detached HEAD state?",
        response_text="Use git checkout main or git switch -c new-branch",
        category="Git & Version Control",
        subcategory="Branching",
        difficulty="Intermediate",
        tags=["git", "head", "vcs"]
    )
    assert isinstance(query_id, int)
    assert query_id > 0

    # Test feedback
    database.add_feedback(query_id=query_id, telegram_id=test_id, rating=1, comment="Super clear!")

    # Test stats
    stats = database.get_community_stats()
    assert stats["total_students"] >= 1
    assert stats["total_doubts_resolved"] >= 1

    # Test recent queries
    recents = database.get_recent_queries(limit=5)
    assert len(recents) >= 1
    assert any(q["id"] == query_id for q in recents)

# ==================== 2. AI ANALYZER & CLASSIFICATION TESTS ====================

def test_ai_analyzer_text_query_classification():
    """Tests AI categorization across key FOSS domains."""
    analyzer = AIAnalyzer()

    # Test Git query
    git_res = analyzer.analyze_text_query("How do I resolve a Git rebase merge conflict?")
    assert git_res["category"] == "Git & Version Control"
    assert "git" in git_res["tags"]
    assert len(git_res["direct_answer"]) > 20

    # Test Linux query
    linux_res = analyzer.analyze_text_query("What does chmod 755 do in Linux terminal?")
    assert linux_res["category"] == "Linux & Shell Scripting"
    assert "chmod" in linux_res["direct_answer"] or "permission" in linux_res["direct_answer"].lower()

    # Test Licensing query
    license_res = analyzer.analyze_text_query("Is GNU GPLv3 copyleft and what makes it different from MIT?")
    assert license_res["category"] == "Open Source Licensing & Ethics"
    assert "GPL" in license_res["direct_answer"] or "Copyleft" in license_res["direct_answer"]

    # Test GSoC query
    gsoc_res = analyzer.analyze_text_query("How can I prepare for Google Summer of Code (GSoC) as a student?")
    assert gsoc_res["category"] == "Open Source Programs & GSoC"
    assert "GSoC" in gsoc_res["direct_answer"] or "issue" in gsoc_res["direct_answer"].lower()

    # Test Debugging query
    bug_res = analyzer.analyze_text_query("Getting Segmentation fault (core dumped) in C program")
    assert bug_res["category"] == "Programming & Bug Debugging"

def test_ai_analyzer_classify_shortcut():
    """Tests the structured taxonomy classification shortcut."""
    analyzer = AIAnalyzer()
    res = analyzer.classify_query("How to set up Docker container for self-hosting?")
    assert res["category"] == "DevOps, Docker & Self-Hosting"
    assert "docker" in res["tags"] or "containers" in res["tags"]

# ==================== 3. REPORT FORMATTER & PDF TESTS ====================

def test_telegram_html_formatter():
    """Ensures message formatting produces safe, valid HTML."""
    sample_analysis = {
        "category": "Git & Version Control",
        "subcategory": "Merge Conflicts",
        "difficulty": "Intermediate",
        "summary": "Fixing git conflict in file.py",
        "direct_answer": "Open the file and remove conflict markers.",
        "terminal_commands_or_code": "git add file.py\ngit rebase --continue",
        "recommended_foss_tools": ["LazyGit", "Git"],
        "foss_tip": "Keep branch histories clean with interactive rebase.",
        "tags": ["git", "rebase"]
    }

    formatted = format_telegram_response(sample_analysis, query_id=42)
    assert "Category:</b> Git &amp; Version Control" in formatted
    assert "<pre><code>git add file.py" in formatted
    assert "git rebase --continue" in formatted
    assert "#42" in formatted

def test_report_generation_file_creation(tmp_path):
    """Verifies report generation outputs a valid document."""
    sample_analysis = {
        "category": "Linux & Shell Scripting",
        "subcategory": "Permissions",
        "difficulty": "Beginner",
        "direct_answer": "Permissions are broken into read, write, and execute bits.",
        "terminal_commands_or_code": "chmod +x deploy.sh",
        "recommended_foss_tools": ["GNU Coreutils"],
        "foss_tip": "Check permissions with ls -l."
    }

    report_path = generate_pdf_report(
        analysis=sample_analysis,
        query_text="How to make a bash script executable?",
        output_filename="test_report.pdf",
        student_name="Test Hacker"
    )
    assert os.path.exists(report_path)
    assert os.path.getsize(report_path) > 0

# ==================== 4. FASTAPI ENDPOINT TESTS ====================

def test_fastapi_endpoints():
    """Tests the lightweight evaluator REST API."""
    client = TestClient(app)

    # Health check
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # Community Stats
    res_stats = client.get("/api/stats")
    assert res_stats.status_code == 200
    data_stats = res_stats.json()
    assert "total_students" in data_stats
    assert "total_doubts_resolved" in data_stats

    # Classify API
    res_classify = client.post("/api/classify", json={"query": "Difference between GPL and MIT"})
    assert res_classify.status_code == 200
    data_classify = res_classify.json()
    assert data_classify["category"] == "Open Source Licensing & Ethics"

    # Ask API
    res_ask = client.post("/api/ask", json={"query": "How do I stash my changes in Git?"})
    assert res_ask.status_code == 200
    data_ask = res_ask.json()
    assert "query_id" in data_ask
    assert data_ask["analysis"]["category"] == "Git & Version Control"

    # Curated Resources
    res_resource = client.get("/api/resources/git")
    assert res_resource.status_code == 200
    assert "git clone" in res_resource.json()["content"]

# ==================== 5. TELEGRAM BOT APP REGISTRATION ====================

def test_telegram_bot_builder():
    """Verifies Telegram bot registers handlers without exceptions."""
    bot_app = build_bot_application()
    assert bot_app is not None
    # Handlers registered
    assert len(bot_app.handlers) > 0
