"""SQLite persistence for conversations, attachments and local token usage."""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "nautilus.sqlite3"
UPLOAD_DIR = DATA_DIR / "uploads"
WINDOW_SECONDS = 3 * 60 * 60
PLAN_LIMITS = {"free": 300_000, "pro": 1_000_000, "max": 3_000_000}
PLAN_NAMES = {"free": "Standard", "pro": "Esteso", "max": "Massimo"}
DEFAULT_PLAN = "free"
DEFAULT_TOKEN_LIMIT = PLAN_LIMITS[DEFAULT_PLAN]
ALLOWED_LIMITS = set(PLAN_LIMITS.values())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT 'Nuova conversazione',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                attachments_json TEXT NOT NULL DEFAULT '[]',
                FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, id);
            CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC);
            CREATE TABLE IF NOT EXISTS usage_state (
                id INTEGER PRIMARY KEY CHECK(id=1),
                window_started_at REAL NOT NULL,
                tokens_used INTEGER NOT NULL DEFAULT 0,
                token_limit INTEGER NOT NULL DEFAULT 300000,
                plan TEXT NOT NULL DEFAULT 'free'
            );
            CREATE TABLE IF NOT EXISTS usage_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at REAL NOT NULL,
                prompt_tokens INTEGER NOT NULL DEFAULT 0,
                completion_tokens INTEGER NOT NULL DEFAULT 0,
                total_tokens INTEGER NOT NULL DEFAULT 0,
                mode TEXT NOT NULL DEFAULT 'ollama',
                conversation_id TEXT
            );
        """)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(messages)").fetchall()}
        if "feedback" not in columns:
            conn.execute("ALTER TABLE messages ADD COLUMN feedback TEXT NOT NULL DEFAULT ''")
        columns = {row[1] for row in conn.execute("PRAGMA table_info(messages)")}
        if "attachments_json" not in columns:
            conn.execute("ALTER TABLE messages ADD COLUMN attachments_json TEXT NOT NULL DEFAULT '[]'")
        usage_columns = {row[1] for row in conn.execute("PRAGMA table_info(usage_state)")}
        if "plan" not in usage_columns:
            conn.execute("ALTER TABLE usage_state ADD COLUMN plan TEXT NOT NULL DEFAULT 'free'")
            # Migrate previous 2-hour local usage settings to the new Free tier.
            conn.execute("UPDATE usage_state SET plan='free', token_limit=?", (DEFAULT_TOKEN_LIMIT,))
        conn.execute(
            "INSERT OR IGNORE INTO usage_state(id,window_started_at,tokens_used,token_limit,plan) VALUES(1,?,0,?,'free')",
            (time.time(), DEFAULT_TOKEN_LIMIT),
        )
        # Align limits stored by earlier versions with the current tier values.
        for plan_key, plan_limit in PLAN_LIMITS.items():
            conn.execute("UPDATE usage_state SET token_limit=? WHERE plan=?", (plan_limit, plan_key))


def create_conversation(title: str = "Nuova conversazione") -> dict[str, Any]:
    conversation_id = uuid.uuid4().hex
    now = utc_now()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO conversations(id,title,created_at,updated_at) VALUES(?,?,?,?)",
            (conversation_id, title[:90], now, now),
        )
    return get_conversation(conversation_id) or {}


def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id,title,created_at,updated_at FROM conversations WHERE id=?", (conversation_id,)
        ).fetchone()
    return dict(row) if row else None


def list_conversations() -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("""
            SELECT c.id,c.title,c.created_at,c.updated_at,
                   (SELECT content FROM messages m WHERE m.conversation_id=c.id ORDER BY m.id DESC LIMIT 1) AS preview,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id=c.id) AS message_count
            FROM conversations c ORDER BY c.updated_at DESC
        """).fetchall()
    return [dict(row) for row in rows]


def add_message(conversation_id: str, role: str, content: str,
                attachments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if role not in {"user", "assistant", "system"}:
        raise ValueError("Ruolo non valido")
    now = utc_now()
    safe_attachments = attachments if isinstance(attachments, list) else []
    with _connect() as conn:
        exists = conn.execute("SELECT 1 FROM conversations WHERE id=?", (conversation_id,)).fetchone()
        if not exists:
            raise KeyError("Conversazione inesistente")
        cursor = conn.execute(
            "INSERT INTO messages(conversation_id,role,content,created_at,attachments_json) VALUES(?,?,?,?,?)",
            (conversation_id, role, content, now, json.dumps(safe_attachments, ensure_ascii=False)),
        )
        conn.execute("UPDATE conversations SET updated_at=? WHERE id=?", (now, conversation_id))
        row = conn.execute("SELECT * FROM messages WHERE id=?", (cursor.lastrowid,)).fetchone()
    return _message_from_row(row)


def _message_from_row(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    try:
        attachments = json.loads(result.pop("attachments_json", "[]"))
    except (ValueError, TypeError):
        attachments = []
    result["attachments"] = attachments if isinstance(attachments, list) else []
    return result


def get_messages(conversation_id: str, limit: int | None = None) -> list[dict[str, Any]]:
    with _connect() as conn:
        if limit is None:
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id=? ORDER BY id", (conversation_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM (SELECT * FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?) ORDER BY id",
                (conversation_id, limit),
            ).fetchall()
    return [_message_from_row(row) for row in rows]


def rename_conversation(conversation_id: str, title: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE conversations SET title=?,updated_at=? WHERE id=?",
            (title.strip()[:90] or "Nuova conversazione", utc_now(), conversation_id),
        )
    return cursor.rowcount > 0


def delete_conversation(conversation_id: str) -> bool:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT attachments_json FROM messages WHERE conversation_id=?", (conversation_id,)
        ).fetchall()
        cursor = conn.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))
    if cursor.rowcount:
        for row in rows:
            try:
                for attachment in json.loads(row[0] or "[]"):
                    delete_upload(attachment.get("id", ""))
            except (ValueError, TypeError, AttributeError):
                pass
    return cursor.rowcount > 0


def database_stats() -> dict[str, int]:
    with _connect() as conn:
        conversations = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    return {"conversations": int(conversations), "messages": int(messages)}


def _roll_usage(conn: sqlite3.Connection, now: float | None = None) -> sqlite3.Row:
    current = time.time() if now is None else now
    row = conn.execute("SELECT * FROM usage_state WHERE id=1").fetchone()
    if row is None:
        conn.execute("INSERT INTO usage_state(id,window_started_at,tokens_used,token_limit,plan) VALUES(1,?,0,?,'free')",
                     (current, DEFAULT_TOKEN_LIMIT))
        row = conn.execute("SELECT * FROM usage_state WHERE id=1").fetchone()
    elif current >= float(row["window_started_at"]) + WINDOW_SECONDS:
        # Fixed three-hour local window: usage becomes available again at reset time.
        conn.execute("UPDATE usage_state SET window_started_at=?,tokens_used=0 WHERE id=1", (current,))
        row = conn.execute("SELECT * FROM usage_state WHERE id=1").fetchone()
    return row


def usage_snapshot() -> dict[str, Any]:
    now = time.time()
    with _connect() as conn:
        row = _roll_usage(conn, now)
    start = float(row["window_started_at"])
    limit = int(row["token_limit"])
    used = int(row["tokens_used"])
    reset_at = start + WINDOW_SECONDS
    remaining_seconds = max(0, int(reset_at - now))
    plan = str(row["plan"] or DEFAULT_PLAN)
    if plan not in PLAN_LIMITS:
        plan = DEFAULT_PLAN
    return {
        "plan": plan,
        "plan_name": PLAN_NAMES[plan],
        "plan_limit": PLAN_LIMITS[plan],
        "tokens_used": used,
        "token_limit": limit,
        "remaining_tokens": max(0, limit - used),
        "window_seconds": WINDOW_SECONDS,
        "window_started_at": datetime.fromtimestamp(start, timezone.utc).isoformat(timespec="seconds"),
        "reset_at": datetime.fromtimestamp(reset_at, timezone.utc).isoformat(timespec="seconds"),
        "seconds_until_reset": remaining_seconds,
        "percent_used": round(min(100, used * 100 / limit), 1) if limit else 100,
        "limited": used >= limit,
        "is_local_policy": True,
        "window_hours": 3,
        "billing_enabled": False,
    }


def set_usage_plan(plan: str) -> dict[str, Any]:
    plan = str(plan).lower().strip()
    if plan not in PLAN_LIMITS:
        raise ValueError("Limite non valido. Scegli Standard, Esteso o Massimo.")
    with _connect() as conn:
        _roll_usage(conn)
        conn.execute("UPDATE usage_state SET plan=?,token_limit=? WHERE id=1", (plan, PLAN_LIMITS[plan]))
    return usage_snapshot()


def set_usage_limit(limit: int) -> dict[str, Any]:
    # Backwards-compatible endpoint for old settings; only plan-tier limits are allowed.
    if limit not in ALLOWED_LIMITS:
        raise ValueError(f"Il limite deve corrispondere a uno dei piani: {', '.join(str(x) for x in sorted(ALLOWED_LIMITS))} token ogni 3 ore.")
    with _connect() as conn:
        row = _roll_usage(conn)
        plan = next((key for key, value in PLAN_LIMITS.items() if value == limit), DEFAULT_PLAN)
        conn.execute("UPDATE usage_state SET plan=?,token_limit=? WHERE id=1", (plan, limit))
    return usage_snapshot()


def charge_usage(prompt_tokens: int, completion_tokens: int, mode: str,
                 conversation_id: str | None = None) -> dict[str, Any]:
    prompt = max(0, int(prompt_tokens))
    completion = max(0, int(completion_tokens))
    total = prompt + completion
    now = time.time()
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        _roll_usage(conn, now)
        conn.execute("UPDATE usage_state SET tokens_used=tokens_used+? WHERE id=1", (total,))
        conn.execute(
            "INSERT INTO usage_events(created_at,prompt_tokens,completion_tokens,total_tokens,mode,conversation_id) VALUES(?,?,?,?,?,?)",
            (now, prompt, completion, total, mode[:40], conversation_id),
        )
    return usage_snapshot()


def recent_usage_events(limit: int = 20) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT created_at,prompt_tokens,completion_tokens,total_tokens,mode FROM usage_events ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 100)),),
        ).fetchall()
    return [dict(row) for row in rows]


def upload_path(file_id: str) -> Path | None:
    if len(file_id) != 32 or any(ch not in "0123456789abcdef" for ch in file_id):
        return None
    for suffix in (".png", ".jpg", ".webp"):
        path = UPLOAD_DIR / f"{file_id}{suffix}"
        if path.is_file():
            return path
    return None


def delete_upload(file_id: str) -> None:
    path = upload_path(file_id)
    if path:
        try:
            path.unlink()
        except OSError:
            pass


def list_image_attachments(limit: int = 500) -> list[dict[str, Any]]:
    """List image attachments in saved chats for the unified local gallery."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT m.conversation_id,m.content,m.created_at,m.attachments_json FROM messages m "
            "WHERE m.attachments_json != '[]' ORDER BY m.id DESC LIMIT ?",
            (max(1, min(int(limit), 2000)),),
        ).fetchall()
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        try:
            attachments = json.loads(row["attachments_json"] or "[]")
        except (ValueError, TypeError):
            continue
        if not isinstance(attachments, list):
            continue
        for attachment in attachments:
            if not isinstance(attachment, dict):
                continue
            image_id = str(attachment.get("id", ""))
            if not image_id or image_id in seen:
                continue
            path = upload_path(image_id)
            if not path:
                continue
            mime = str(attachment.get("mime") or "")
            if not mime.startswith("image/"):
                continue
            seen.add(image_id)
            result.append({
                "id": image_id,
                "conversation_id": str(row["conversation_id"]),
                "content": str(row["content"] or ""),
                "created_at": str(row["created_at"] or ""),
                "name": str(attachment.get("name") or path.name),
                "mime": mime,
                "size": int(attachment.get("size", path.stat().st_size)),
                "url": f"/api/files/{image_id}",
            })
    return result


def truncate_messages(conversation_id: str, keep: int) -> int:
    """Delete every message after the first `keep` ones (used by edit and regenerate)."""
    keep = max(0, int(keep))
    with _connect() as conn:
        ids = [row[0] for row in conn.execute("SELECT id FROM messages WHERE conversation_id=? ORDER BY id", (conversation_id,)).fetchall()]
        doomed = ids[keep:]
        for message_id in doomed:
            conn.execute("DELETE FROM messages WHERE id=?", (message_id,))
        if doomed:
            conn.execute("UPDATE conversations SET updated_at=? WHERE id=?", (utc_now(), conversation_id))
    return len(doomed)


def set_feedback(message_id: int, value: str) -> bool:
    if value not in {"", "up", "down"}:
        raise ValueError("Valore di feedback non valido")
    with _connect() as conn:
        cursor = conn.execute("UPDATE messages SET feedback=? WHERE id=? AND role='assistant'", (value, int(message_id)))
    return cursor.rowcount > 0
