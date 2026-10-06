import os
from flask import request, jsonify
from twilio.request_validator import RequestValidator

from config import TWILIO_AUTH_TOKEN, WHATSAPP_ADMIN_ID
from services.whatsapp_service import send_whatsapp_message
from services.github_service import fetch_repo_summary
from services.system_service import get_system_status
from bot import backup_task, github_monitor_task, system_health_task


def handle_whatsapp_command(command: str, sender: str) -> str:
    if not sender.endswith(WHATSAPP_ADMIN_ID.replace('whatsapp:', '')) and WHATSAPP_ADMIN_ID:
        return "❌ Access denied."

    cmd = command.strip().lower()

    if cmd in ["/status", "status"]:
        return "✅ AI-Bot is running and monitoring tasks."

    if cmd in ["/github", "github"]:
        repo = fetch_repo_summary("vinit-cyber-lab/AI-Bot")
        if not repo:
            return "❌ GitHub data unavailable."
        return (
            f"Repository: {repo.get('full_name', 'N/A')}\n"
            f"Stars: {repo.get('stargazers_count', 0)}\n"
            f"Forks: {repo.get('forks_count', 0)}\n"
            f"Open Issues: {repo.get('open_issues_count', 0)}"
        )

    if cmd in ["/health", "health"]:
        stats = get_system_status()
        if not stats:
            return "❌ Health data unavailable."
        return (
            f"CPU: {stats.get('cpu_percent', 0)}%\n"
            f"Memory: {stats.get('memory_percent', 0)}%\n"
            f"Disk: {stats.get('disk_percent', 0)}%"
        )

    if cmd in ["/backup", "backup"]:
        backup_task()
        return "✅ Backup task triggered."

    if cmd in ["/logs", "logs"]:
        try:
            with open("logs/bot.log", "r", encoding="utf-8") as file:
                lines = file.readlines()[-10:]
            return "".join(lines) or "No logs available yet."
        except Exception:
            return "No logs found yet."

    if cmd in ["/help", "help"]:
        return (
            "Available commands:\n"
            "/status\n"
            "/github\n"
            "/health\n"
            "/backup\n"
            "/logs\n"
            "/help"
        )

    if cmd == "/run github":
        github_monitor_task()
        return "✅ GitHub task executed."

    if cmd == "/run health":
        system_health_task()
        return "✅ Health task executed."

    if cmd == "/run backup":
        backup_task()
        return "✅ Backup task executed."

    return "Unknown command. Send /help to see available commands."


def validate_twilio_request():
    token = TWILIO_AUTH_TOKEN
    if not token:
        return True

    validator = RequestValidator(token)
    url = request.url
    form = request.form
    signature = request.headers.get('X-Twilio-Signature', '')
    return validator.validate(url, form, signature)


def whatsapp_webhook():
    if not validate_twilio_request():
        return "Unauthorized", 403

    sender = request.form.get("From", "")
    body = request.form.get("Body", "").strip()
    response = handle_whatsapp_command(body, sender)
    send_whatsapp_message(response, sender)
    return "OK", 200
