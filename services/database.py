import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/aibot.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_database():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            platform_user_id TEXT UNIQUE NOT NULL,
            phone_number TEXT,
            display_name TEXT,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_seen TEXT,
            metadata TEXT
        )
    """
    )

    # Audit log table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            target TEXT,
            details TEXT,
            success BOOLEAN DEFAULT 1,
            ip_address TEXT,
            metadata TEXT
        )
    """
    )

    # Settings table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT
        )
    """
    )

    # Moderation events table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS moderation_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            reason TEXT,
            moderator TEXT,
            duration_minutes INTEGER,
            active BOOLEAN DEFAULT 1,
            metadata TEXT
        )
    """
    )

    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect(str(DB_PATH))


def add_user(source: str, platform_user_id: str, display_name: str = "", phone_number: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (source, platform_user_id, display_name, phone_number)
            VALUES (?, ?, ?, ?)
        """,
            (source, platform_user_id, display_name, phone_number),
        )
        conn.commit()
        return {"success": True, "id": cursor.lastrowid}
    except sqlite3.IntegrityError:
        cursor.execute(
            "UPDATE users SET display_name = ?, phone_number = ? WHERE platform_user_id = ?",
            (display_name, phone_number, platform_user_id),
        )
        conn.commit()
        return {"success": True, "message": "User updated"}
    finally:
        conn.close()


def get_user(platform_user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE platform_user_id = ?", (platform_user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "source": row[1],
        "platform_user_id": row[2],
        "phone_number": row[3],
        "display_name": row[4],
        "role": row[5],
        "status": row[6],
        "created_at": row[7],
        "last_seen": row[8],
    }


def list_users(limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "source": row[1],
            "platform_user_id": row[2],
            "phone_number": row[3],
            "display_name": row[4],
            "role": row[5],
            "status": row[6],
            "created_at": row[7],
            "last_seen": row[8],
        }
        for row in rows
    ]


def update_user_status(platform_user_id: str, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = ? WHERE platform_user_id = ?", (status, platform_user_id))
    conn.commit()
    conn.close()
    return {"success": True, "status": status}


def update_user_role(platform_user_id: str, role: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE platform_user_id = ?", (role, platform_user_id))
    conn.commit()
    conn.close()
    return {"success": True, "role": role}


def log_audit(action: str, actor: str, target: str = "", details: str = "", success: bool = True, ip_address: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO audit_log (action, actor, target, details, success, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (action, actor, target, details, success, ip_address),
    )
    conn.commit()
    conn.close()
    return {"success": True, "timestamp": datetime.utcnow().isoformat()}


def get_audit_logs(limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, timestamp, action, actor, target, details, success FROM audit_log ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": row[0], "timestamp": row[1], "action": row[2], "actor": row[3], "target": row[4], "details": row[5], "success": row[6]}
        for row in rows
    ]


def log_moderation_event(user_id: str, action: str, reason: str = "", moderator: str = "", duration_minutes: int = 0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO moderation_events (user_id, action, reason, moderator, duration_minutes)
        VALUES (?, ?, ?, ?, ?)
    """,
        (user_id, action, reason, moderator, duration_minutes),
    )
    conn.commit()
    conn.close()
    return {"success": True, "timestamp": datetime.utcnow().isoformat()}


def get_moderation_events(user_id: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT * FROM moderation_events WHERE user_id = ? AND active = 1 ORDER BY timestamp DESC", (user_id,))
    else:
        cursor.execute("SELECT * FROM moderation_events WHERE active = 1 ORDER BY timestamp DESC LIMIT 100")
    rows = cursor.fetchall()
    conn.close()
    return rows


def save_setting(key: str, value: str, updated_by: str = "system"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO settings (key, value, updated_by, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """,
        (key, value, updated_by),
    )
    conn.commit()
    conn.close()
    return {"success": True, "key": key, "value": value}


def get_setting(key: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def list_settings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")
