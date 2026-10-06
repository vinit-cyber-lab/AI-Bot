import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = os.getenv("BOT_NAME", "AI-Bot")
BOT_VERSION = os.getenv("BOT_VERSION", "1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

GITHUB_REPO = os.getenv("GITHUB_REPO", "vinit-cyber-lab/AI-Bot")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

GITHUB_CHECK_INTERVAL_MINUTES = int(os.getenv("GITHUB_CHECK_INTERVAL_MINUTES", "5"))
HEALTH_CHECK_INTERVAL_MINUTES = int(os.getenv("HEALTH_CHECK_INTERVAL_MINUTES", "10"))
BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "1"))
DAILY_SUMMARY_TIME = os.getenv("DAILY_SUMMARY_TIME", "09:00")
APP_ENV = os.getenv("APP_ENV", "development")
