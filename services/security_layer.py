import sqlite3
from datetime import datetime
from pathlib import Path

LOG_PATH = Path("logs/admin_security.log")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_security_event(event_type: str, actor: str, action: str, resource: str = "", result: str = "success", details: str = ""):
    timestamp = datetime.utcnow().isoformat() + "Z"
    entry = f"[{timestamp}] TYPE={event_type} ACTOR={actor} ACTION={action} RESOURCE={resource} RESULT={result} DETAILS={details}"
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(entry + "\n")
    return {"timestamp": timestamp, "logged": True}


def read_security_log(limit: int = 50):
    if not LOG_PATH.exists():
        return []
    rows = []
    with LOG_PATH.open("r", encoding="utf-8") as handle:
        for line in handle.readlines()[-limit:]:
            rows.append(line.strip())
    return rows


def check_rate_limit(key: str, limit: int = 5, window_seconds: int = 60) -> bool:
    from services.database import get_connection
    import time
    conn = get_connection()
    cursor = conn.cursor()
    now = time.time()
    cursor.execute(
        "SELECT COUNT(*) FROM audit_log WHERE actor = ? AND timestamp > datetime('now', '-' || ? || ' seconds')",
        (key, window_seconds),
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count < limit
