import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import DATABASE_PATH

def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initialize database tables with schema migrations."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                role TEXT DEFAULT 'student',
                doubt_count INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Queries / Doubts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                query_type TEXT DEFAULT 'text', -- 'text' or 'photo'
                query_text TEXT NOT NULL,
                image_path TEXT,
                category TEXT DEFAULT 'General FOSS',
                subcategory TEXT DEFAULT 'General',
                difficulty TEXT DEFAULT 'Beginner', -- 'Beginner', 'Intermediate', 'Advanced'
                tags TEXT DEFAULT '[]', -- JSON string of tags
                response_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE SET NULL
            )
        """)

        # User Feedback Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER,
                telegram_id INTEGER,
                rating INTEGER, -- 1 for upvote, -1 for downvote
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES queries(id) ON DELETE CASCADE
            )
        """)

        # Curated Resources / Cheatsheets Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT UNIQUE,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Pre-seed initial resources if not present
        cursor.execute("SELECT COUNT(*) FROM resources")
        if cursor.fetchone()[0] == 0:
            initial_resources = [
                (
                    "git",
                    "FOSS Git & Version Control Quick Reference",
                    "• git init: Initialize a repo\n• git clone <url>: Clone repository\n• git checkout -b <branch>: Create and switch branch\n• git add -A: Stage all changes\n• git commit -m 'feat: message': Conventional commit\n• git pull --rebase origin main: Sync changes smoothly\n• git push origin <branch>: Push to remote"
                ),
                (
                    "linux",
                    "Linux Command & System Administration Essentials",
                    "• sudo apt update && sudo apt upgrade: Update Debian/Ubuntu packages\n• systemctl status <service>: Check service status\n• journalctl -xeu <service>: Debug service logs\n• chmod +x <script.sh>: Make script executable\n• grep -rnw './' -e 'keyword': Search recursively in files\n• htop / btop: Real-time terminal system monitor"
                ),
                (
                    "licenses",
                    "Open Source Licensing Guide",
                    "• MIT: Highly permissive. Anyone can use, modify, and distribute commercially.\n• Apache 2.0: Permissive with explicit patent protection grants.\n• GNU GPLv3: Strong Copyleft. Derivative works must also be open source under GPL.\n• AGPLv3: Network-triggered Copyleft. Ideal for web services.\n• BSD 2/3-Clause: Permissive, simple, requires notice preservation."
                ),
                (
                    "programs",
                    "Open Source Programs & Mentorships",
                    "• Google Summer of Code (GSoC): Global program with stipends for open source contributors.\n• Hacktoberfest: Annual October celebration by DigitalOcean to encourage first PRs.\n• Outreachy: 3-month paid remote internships for underrepresented groups in tech.\n• LFX Mentorship: Linux Foundation mentorship projects in Cloud Native & Linux kernel."
                )
            ]
            cursor.executemany(
                "INSERT INTO resources (topic, title, content) VALUES (?, ?, ?)",
                initial_resources
            )

        conn.commit()

def register_or_update_user(telegram_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str] = None):
    """Registers a new user or updates their last active timestamp."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (telegram_id, username, first_name, last_name, doubt_count, last_active_at)
            VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                doubt_count = users.doubt_count + 1,
                last_active_at = CURRENT_TIMESTAMP
        """, (telegram_id, username, first_name, last_name))
        conn.commit()

def log_query(
    telegram_id: Optional[int],
    query_type: str,
    query_text: str,
    response_text: str,
    category: str = "General FOSS",
    subcategory: str = "General",
    difficulty: str = "Beginner",
    tags: Optional[List[str]] = None,
    image_path: Optional[str] = None
) -> int:
    """Logs a query/answer pair into the database and returns the generated query ID."""
    tags_json = json.dumps(tags if tags else [])
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO queries (
                telegram_id, query_type, query_text, image_path,
                category, subcategory, difficulty, tags, response_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            telegram_id, query_type, query_text, image_path,
            category, subcategory, difficulty, tags_json, response_text
        ))
        conn.commit()
        return cursor.lastrowid

def get_community_stats() -> Dict[str, Any]:
    """Computes aggregated metrics for the FOSS MBCCET community."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Total Users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        # Total Queries
        cursor.execute("SELECT COUNT(*) FROM queries")
        total_queries = cursor.fetchone()[0]

        # Photo/Screenshot Queries
        cursor.execute("SELECT COUNT(*) FROM queries WHERE query_type = 'photo'")
        photo_queries = cursor.fetchone()[0]

        # Breakdown by Category
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM queries 
            GROUP BY category 
            ORDER BY count DESC
        """)
        categories = [{"category": row["category"], "count": row["count"]} for row in cursor.fetchall()]

        # Breakdown by Difficulty
        cursor.execute("""
            SELECT difficulty, COUNT(*) as count 
            FROM queries 
            GROUP BY difficulty 
            ORDER BY count DESC
        """)
        difficulty = [{"level": row["difficulty"], "count": row["count"]} for row in cursor.fetchall()]

        # Active contributors/students
        cursor.execute("""
            SELECT username, first_name, doubt_count, last_active_at 
            FROM users 
            ORDER BY doubt_count DESC 
            LIMIT 5
        """)
        top_inquirers = [dict(row) for row in cursor.fetchall()]

        return {
            "total_students": total_users,
            "total_doubts_resolved": total_queries,
            "code_screenshots_analyzed": photo_queries,
            "categories": categories,
            "difficulty_breakdown": difficulty,
            "top_learners": top_inquirers
        }

def get_recent_queries(limit: int = 15) -> List[Dict[str, Any]]:
    """Fetches the most recent solved doubts for the dashboard and bot feed."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.id, q.telegram_id, u.first_name, u.username, q.query_type,
                   q.query_text, q.category, q.subcategory, q.difficulty,
                   q.tags, q.created_at, substr(q.response_text, 1, 150) as snippet
            FROM queries q
            LEFT JOIN users u ON q.telegram_id = u.telegram_id
            ORDER BY q.created_at DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            item = dict(row)
            try:
                item["tags"] = json.loads(item["tags"])
            except Exception:
                item["tags"] = []
            results.append(item)
        return results

def get_resource(topic: str) -> Optional[Dict[str, str]]:
    """Retrieves curated cheat sheets or guides by topic slug."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT topic, title, content FROM resources WHERE topic = ?", (topic.lower(),))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def add_feedback(query_id: int, telegram_id: int, rating: int, comment: Optional[str] = None):
    """Logs user feedback (helpful or not)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO feedback (query_id, telegram_id, rating, comment)
            VALUES (?, ?, ?, ?)
        """, (query_id, telegram_id, rating, comment))
        conn.commit()
