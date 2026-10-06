import json
import os
import time
from datetime import datetime

import schedule

from config import (
    APP_ENV,
    BACKUP_INTERVAL_HOURS,
    BOT_NAME,
    BOT_VERSION,
    DAILY_SUMMARY_TIME,
    DISCORD_WEBHOOK_URL,
    GITHUB_CHECK_INTERVAL_MINUTES,
    GITHUB_REPO,
    HEALTH_CHECK_INTERVAL_MINUTES,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from services.github_service import fetch_repo_summary
from services.notifications import send_all
from services.system_service import get_system_status


BACKUP_DIR = "backups"
LOG_DIR = "logs"
DATA_DIR = "data"


def ensure_directories():
    for directory in [BACKUP_DIR, LOG_DIR, DATA_DIR]:
        os.makedirs(directory, exist_ok=True)


def create_backup_file() -> str:
    ensure_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.json")
    payload = {
        "timestamp": datetime.now().isoformat(),
        "bot_name": BOT_NAME,
        "bot_version": BOT_VERSION,
        "application_env": APP_ENV,
        "status": "healthy",
    }
    with open(backup_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
    return backup_path


def github_monitor_task():
    repo_info = fetch_repo_summary(GITHUB_REPO)
    if not repo_info:
        message = f"[{BOT_NAME}] GitHub monitor failed: no data returned."
        send_all(message)
        return

    message = (
        f"[{BOT_NAME}] GitHub status\n"
        f"Repository: {repo_info.get('full_name', GITHUB_REPO)}\n"
        f"Default branch: {repo_info.get('default_branch', 'unknown')}\n"
        f"Open issues: {repo_info.get('open_issues_count', 0)}\n"
        f"Stars: {repo_info.get('stargazers_count', 0)}\n"
        f"Forks: {repo_info.get('forks_count', 0)}\n"
        f"Last push: {repo_info.get('pushed_at', 'unknown')}\n"
        f"Visibility: {repo_info.get('visibility', 'unknown')}"
    )
    print(message)
    send_all(message)


def system_health_task():
    stats = get_system_status()
    if not stats:
        message = f"[{BOT_NAME}] System health check failed."
        send_all(message)
        return

    message = (
        f"[{BOT_NAME}] System health\n"
        f"CPU: {stats.get('cpu_percent', 0)}%\n"
        f"Memory: {stats.get('memory_percent', 0)}%\n"
        f"Disk: {stats.get('disk_percent', 0)}%\n"
        f"Platform: {stats.get('platform', 'unknown')}"
    )
    print(message)
    send_all(message)


def backup_task():
    backup_path = create_backup_file()
    message = f"[{BOT_NAME}] Backup created successfully: {backup_path}"
    print(message)
    send_all(message)


def daily_summary_task():
    repo_info = fetch_repo_summary(GITHUB_REPO)
    system_stats = get_system_status()
    repo_name = repo_info.get("full_name", GITHUB_REPO) if repo_info else GITHUB_REPO
    system_line = (
        f"CPU: {system_stats.get('cpu_percent', 0)}% | "
        f"Memory: {system_stats.get('memory_percent', 0)}% | "
        f"Disk: {system_stats.get('disk_percent', 0)}%"
    )
    message = (
        f"[{BOT_NAME}] Daily summary\n"
        f"Repository: {repo_name}\n"
        f"Open issues: {repo_info.get('open_issues_count', 0) if repo_info else 'n/a'}\n"
        f"Stars: {repo_info.get('stargazers_count', 0) if repo_info else 'n/a'}\n"
        f"System: {system_line}"
    )
    print(message)
    send_all(message)


def schedule_tasks():
    schedule.every(GITHUB_CHECK_INTERVAL_MINUTES).minutes.do(github_monitor_task)
    schedule.every(HEALTH_CHECK_INTERVAL_MINUTES).minutes.do(system_health_task)
    schedule.every(BACKUP_INTERVAL_HOURS).hours.do(backup_task)
    schedule.every().day.at(DAILY_SUMMARY_TIME).do(daily_summary_task)


def startup_notification():
    message = (
        f"[{BOT_NAME}] v{BOT_VERSION} successfully started.\n"
        f"Environment: {APP_ENV}\n"
        f"Watching repo: {GITHUB_REPO}"
    )
    send_all(message)


def run_bot():
    ensure_directories()
    schedule_tasks()
    startup_notification()
    print(f"{BOT_NAME} running. Press Ctrl+C to exit.")

    while True:
        schedule.run_pending()
        time.sleep(5)


if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print(f"{BOT_NAME} shutting down gracefully.")
