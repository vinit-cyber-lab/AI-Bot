import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from functools import wraps

from config import (
    BOT_NAME,
    BOT_VERSION,
    DASHBOARD_HOST,
    DASHBOARD_PORT,
    DASHBOARD_DEBUG,
    GITHUB_REPO,
)
from services.database import (
    init_database,
    add_user,
    list_users,
    update_user_status,
    update_user_role,
    get_audit_logs,
    log_audit,
    log_moderation_event,
    get_moderation_events,
    save_setting,
    list_settings,
)
from services.messaging_adapter import MessagingAdapter, BroadcastAdapter
from services.security_layer import log_security_event
from services.admin_auth import require_admin_auth, require_rate_limit, log_admin_action
from services.github_service import fetch_repo_summary
from services.system_service import get_system_status
from bot import github_monitor_task, system_health_task, backup_task

# Initialize database
init_database()

app = Flask(__name__)
app.secret_key = "ai-bot-secret-key-2024"

LOG_FILE = "logs/bot.log"


def append_log(message: str):
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")


# ============= DASHBOARD ROUTES =============


@app.route("/")
@require_admin_auth
def index():
    status = {
        "bot_name": BOT_NAME,
        "bot_version": BOT_VERSION,
        "status": "running",
        "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return render_template("index.html", status=status)


@app.route("/admin")
@require_admin_auth
def admin_dashboard():
    return render_template("admin_dashboard.html")


# ============= API ENDPOINTS =============


@app.route("/api/status")
@require_admin_auth
def api_status():
    return jsonify(
        {
            "bot_name": BOT_NAME,
            "bot_version": BOT_VERSION,
            "status": "running",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/health")
@require_admin_auth
def api_health():
    stats = get_system_status()
    if not stats:
        return jsonify({"error": "Failed to retrieve system stats"}), 500
    return jsonify(
        {
            "cpu_percent": stats.get("cpu_percent", 0),
            "memory_percent": stats.get("memory_percent", 0),
            "disk_percent": stats.get("disk_percent", 0),
            "platform": stats.get("platform", "unknown"),
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/github")
@require_admin_auth
def api_github():
    repo_info = fetch_repo_summary(GITHUB_REPO)
    if not repo_info:
        return jsonify({"error": f"Failed to fetch repository {GITHUB_REPO}"}), 500
    return jsonify(
        {
            "repository": repo_info.get("full_name", GITHUB_REPO),
            "description": repo_info.get("description", "N/A"),
            "stars": repo_info.get("stargazers_count", 0),
            "forks": repo_info.get("forks_count", 0),
            "open_issues": repo_info.get("open_issues_count", 0),
            "last_push": repo_info.get("pushed_at", "unknown"),
            "url": repo_info.get("html_url", "#"),
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/dashboard")
@require_admin_auth
def api_dashboard():
    repo_info = fetch_repo_summary(GITHUB_REPO)
    system_stats = get_system_status()
    dashboard_data = {
        "bot": {
            "name": BOT_NAME,
            "version": BOT_VERSION,
            "status": "running",
            "timestamp": datetime.now().isoformat(),
        },
        "github": None,
        "system": None,
    }
    if repo_info:
        dashboard_data["github"] = {
            "repository": repo_info.get("full_name", GITHUB_REPO),
            "stars": repo_info.get("stargazers_count", 0),
            "forks": repo_info.get("forks_count", 0),
            "open_issues": repo_info.get("open_issues_count", 0),
        }
    if system_stats:
        dashboard_data["system"] = {
            "cpu_percent": system_stats.get("cpu_percent", 0),
            "memory_percent": system_stats.get("memory_percent", 0),
            "disk_percent": system_stats.get("disk_percent", 0),
        }
    return jsonify(dashboard_data)


# ============= ADMIN ROUTES =============


@app.route("/api/admin/settings", methods=["GET", "POST"])
@require_admin_auth
@require_rate_limit
def admin_settings():
    if request.method == "GET":
        settings = list_settings()
        return jsonify({"settings": settings})

    payload = request.get_json(silent=True) or {}
    key = payload.get("key", "").strip()
    value = payload.get("value", "")

    if not key:
        return jsonify({"error": "Key is required"}), 400

    auth = request.authorization
    actor = auth.username if auth else "system"

    save_setting(key, str(value), actor)
    log_audit("SETTINGS_UPDATE", actor, key, f"Set {key}={value}", success=True)
    log_security_event("SETTINGS_UPDATE", actor, "update_setting", key, "success")

    return jsonify({"success": True, "key": key, "value": str(value)})


@app.route("/api/admin/users", methods=["GET"])
@require_admin_auth
def admin_list_users():
    users = list_users(limit=100)
    return jsonify({"users": users})


@app.route("/api/admin/user/ban", methods=["POST"])
@require_admin_auth
@require_rate_limit
def admin_ban_user():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id", "").strip()
    reason = payload.get("reason", "No reason provided")

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    auth = request.authorization
    actor = auth.username if auth else "system"

    update_user_status(user_id, "banned")
    log_moderation_event(user_id, "ban", reason, actor)
    log_audit("USER_BAN", actor, user_id, reason)
    log_security_event("MODERATION", actor, "ban_user", user_id, "success", reason)

    return jsonify({"success": True, "user_id": user_id, "status": "banned"})


@app.route("/api/admin/user/unban", methods=["POST"])
@require_admin_auth
@require_rate_limit
def admin_unban_user():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id", "").strip()
    reason = payload.get("reason", "No reason provided")

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    auth = request.authorization
    actor = auth.username if auth else "system"

    update_user_status(user_id, "active")
    log_moderation_event(user_id, "unban", reason, actor)
    log_audit("USER_UNBAN", actor, user_id, reason)
    log_security_event("MODERATION", actor, "unban_user", user_id, "success", reason)

    return jsonify({"success": True, "user_id": user_id, "status": "active"})


@app.route("/api/admin/user/role", methods=["POST"])
@require_admin_auth
@require_rate_limit
def admin_assign_role():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id", "").strip()
    role = payload.get("role", "user").strip()

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    auth = request.authorization
    actor = auth.username if auth else "system"

    update_user_role(user_id, role)
    log_audit("ROLE_ASSIGN", actor, user_id, f"Assigned role: {role}")
    log_security_event("ROLE_ASSIGN", actor, "assign_role", user_id, "success", role)

    return jsonify({"success": True, "user_id": user_id, "role": role})


@app.route("/api/admin/broadcast", methods=["POST"])
@require_admin_auth
@require_rate_limit
def admin_broadcast():
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "").strip()
    channels = payload.get("channels", ["discord", "telegram"])

    if not message:
        return jsonify({"error": "Message is required"}), 400

    auth = request.authorization
    actor = auth.username if auth else "system"

    results = BroadcastAdapter.broadcast(message, channels)
    log_audit("BROADCAST", actor, ",".join(channels), message[:50])
    log_security_event("BROADCAST", actor, "send_broadcast", ",".join(channels), "success")

    return jsonify({"success": True, "channels": channels, "results": results})


@app.route("/api/admin/message/send", methods=["POST"])
@require_admin_auth
@require_rate_limit
def admin_send_message():
    payload = request.get_json(silent=True) or {}
    platform = payload.get("platform", "").strip()
    target = payload.get("target", "").strip()
    message = payload.get("message", "").strip()

    if not platform or not target or not message:
        return jsonify({"error": "platform, target, and message required"}), 400

    auth = request.authorization
    actor = auth.username if auth else "system"

    success = MessagingAdapter.send_dm(platform, target, message)
    log_audit("DM_SEND", actor, f"{platform}:{target}", message[:50], success)
    log_security_event("DIRECT_MESSAGE", actor, "send_dm", f"{platform}:{target}", "success" if success else "failed")

    return jsonify({"success": success, "platform": platform, "target": target})


@app.route("/api/admin/server-action", methods=["POST"])
@require_admin_auth
@require_rate_limit
def admin_server_action():
    payload = request.get_json(silent=True) or {}
    action = payload.get("action", "").strip()
    target = payload.get("target", "")
    details = payload.get("details", "")

    if not action:
        return jsonify({"error": "action is required"}), 400

    auth = request.authorization
    actor = auth.username if auth else "system"

    valid_actions = ["toggle_welcome", "toggle_moderation", "toggle_lockdown", "kick_user", "assign_role"]
    if action not in valid_actions:
        return jsonify({"error": f"Invalid action. Valid: {', '.join(valid_actions)}"}), 400

    log_audit("SERVER_ACTION", actor, target, f"Action: {action}")
    log_security_event("SERVER_ACTION", actor, action, target or "none", "success")

    return jsonify({"success": True, "action": action, "target": target, "details": details})


@app.route("/api/admin/audit", methods=["GET"])
@require_admin_auth
def admin_audit_logs():
    limit = request.args.get("limit", 50, type=int)
    logs = get_audit_logs(limit)
    return jsonify({"logs": logs})


@app.route("/api/admin/audit/export", methods=["GET"])
@require_admin_auth
def admin_audit_export():
    logs = get_audit_logs(limit=1000)
    import csv
    from io import StringIO
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "timestamp", "action", "actor", "target", "details", "success"])
    writer.writeheader()
    writer.writerows(logs)
    output.seek(0)
    return send_file(
        StringIO(output.getvalue()).getvalue().encode(),
        mimetype="text/csv",
        as_attachment=True,
        download_name="audit_log.csv",
    )


@app.route("/api/tasks/github", methods=["POST"])
@require_admin_auth
def trigger_github_task():
    try:
        github_monitor_task()
        append_log("Manual GitHub task triggered from dashboard")
        return jsonify({"status": "success", "message": "GitHub task executed"})
    except Exception as exc:
        append_log(f"Manual GitHub task failed: {str(exc)}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/tasks/health", methods=["POST"])
@require_admin_auth
def trigger_health_task():
    try:
        system_health_task()
        append_log("Manual health task triggered from dashboard")
        return jsonify({"status": "success", "message": "Health task executed"})
    except Exception as exc:
        append_log(f"Manual health task failed: {str(exc)}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/tasks/backup", methods=["POST"])
@require_admin_auth
def trigger_backup_task():
    try:
        backup_task()
        append_log("Manual backup task triggered from dashboard")
        return jsonify({"status": "success", "message": "Backup task executed"})
    except Exception as exc:
        append_log(f"Manual backup task failed: {str(exc)}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/logs")
@require_admin_auth
def get_logs():
    lines = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            lines = file.readlines()[-200:]
    return jsonify({"logs": lines})


@app.route("/api/logs/download")
@require_admin_auth
def download_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify({"error": "No log file found"}), 404
    return send_file(LOG_FILE, as_attachment=True, download_name="bot.log")


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as handle:
            handle.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Dashboard started\n")
    print(f"Starting {BOT_NAME} Dashboard...")
    print(f"Access at: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    print(f"Admin Dashboard: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}/admin")
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=DASHBOARD_DEBUG)
