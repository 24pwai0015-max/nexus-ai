import sqlite3
import json
import time
import uuid
import re
from pathlib import Path
from typing import List, Dict, Optional, Any

DB_PATH = Path(__file__).resolve().parent.parent / "nexus_ai.db"

class SessionService:
    """
    SQLite-backed conversation session manager for Nexus AI.
    Provides persistent multi-turn chat threads, history storage, and auto-titling.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    mode TEXT DEFAULT 'auto'
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT DEFAULT '',
                    sources TEXT DEFAULT '[]',
                    created_at REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at ASC);
            """)

    def create_session(self, title: Optional[str] = None, mode: str = "auto") -> Dict[str, Any]:
        session_id = f"chat_{uuid.uuid4().hex[:12]}"
        now = time.time()
        initial_title = title or "New Conversation"

        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (id, title, created_at, updated_at, mode) VALUES (?, ?, ?, ?, ?)",
                (session_id, initial_title, now, now, mode)
            )

        return {
            "id": session_id,
            "title": initial_title,
            "created_at": now,
            "updated_at": now,
            "mode": mode,
            "message_count": 0
        }

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    s.id, 
                    s.title, 
                    s.created_at, 
                    s.updated_at, 
                    s.mode,
                    COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "mode": row["mode"],
                "message_count": row["message_count"]
            }
            for row in rows
        ]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT id, title, created_at, updated_at, mode FROM sessions WHERE id = ?",
                (session_id,)
            ).fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "mode": row["mode"]
            }

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, role, content, intent, sources, created_at 
                FROM messages 
                WHERE session_id = ? 
                ORDER BY created_at ASC, id ASC
            """, (session_id,))
            rows = cursor.fetchall()

        result = []
        for r in rows:
            try:
                sources = json.loads(r["sources"]) if r["sources"] else []
            except Exception:
                sources = []
            result.append({
                "id": r["id"],
                "role": r["role"],
                "content": r["content"],
                "intent": r["intent"],
                "sources": sources,
                "created_at": r["created_at"]
            })
        return result

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: str = "",
        sources: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        now = time.time()
        sources_json = json.dumps(sources or [])

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO messages (session_id, role, content, intent, sources, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, role, content, intent, sources_json, now)
            )
            message_id = cursor.lastrowid

            # Touch session updated_at
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id)
            )

        return {
            "id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "intent": intent,
            "sources": sources or [],
            "created_at": now
        }

    def update_session_title(self, session_id: str, title: str) -> bool:
        clean_title = title.strip()[:60]
        if not clean_title:
            return False
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                (clean_title, time.time(), session_id)
            )
            return cursor.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return cursor.rowcount > 0

    @staticmethod
    def generate_title_from_prompt(prompt: str) -> str:
        """
        Synthesizes a clean, concise ChatGPT-style conversation title from the first prompt.
        """
        cleaned = prompt.strip()
        # Remove common chat filler / command prefixes
        prefixes = [
            r"^(?:search|look\s+up|find)\s+(?:the\s+|for\s+)?",
            r"^(?:generate|create|draw|make)\s+(?:an?\s+)?(?:image|picture|photo)\s+(?:of\s+)?",
            r"^(?:can\s+you\s+)?(?:explain|tell\s+me\s+about|describe)\s+",
            r"^(?:what\s+is|what\s+are|who\s+is|how\s+to|how\s+does)\s+",
            r"^(?:please\s+)",
        ]
        for p in prefixes:
            cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE)

        cleaned = cleaned.strip(" ?.!\"'#*")
        words = cleaned.split()
        if not words:
            return "New Chat"

        title = " ".join(words[:5])
        if len(title) > 36:
            title = title[:33] + "..."
        # Capitalize first letter
        return title[0].upper() + title[1:]

    async def generate_smart_title(self, prompt: str) -> str:
        """
        Synthesizes an intelligent, context-aware 2-4 word title using LLM reasoning.
        Gracefully falls back to heuristic generation if LLM is unavailable.
        """
        try:
            from services.llm_service import llm_service
            title = await llm_service.generate_title(prompt)
            if title and len(title.strip()) > 0:
                return title.strip()
        except Exception:
            pass
        return self.generate_title_from_prompt(prompt)

session_service = SessionService()
