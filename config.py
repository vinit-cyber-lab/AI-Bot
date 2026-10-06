import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = os.getenv("BOT_NAME", "AI-Bot")
BOT_VERSION = os.getenv("BOT_VERSION", "1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

GITHUB_REPO = os.getenv("GITHUB_REPO", "vinit-cyber-lab/AI-Bot")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0") or 0)
DISCORD_ADMIN_ROLE = os.getenv("DISCORD_ADMIN_ROLE", "Admin")
DISCORD_ALLOWED_USER_IDS = os.getenv("DISCORD_ALLOWED_USER_IDS", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

GITHUB_CHECK_INTERVAL_MINUTES = int(os.getenv("GITHUB_CHECK_INTERVAL_MINUTES", "5"))
HEALTH_CHECK_INTERVAL_MINUTES = int(os.getenv("HEALTH_CHECK_INTERVAL_MINUTES", "10"))
BACKUP_INTERVAL_MINUTES = int(os.getenv("BACKUP_INTERVAL_MINUTES", "60"))
BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "1"))
DAILY_SUMMARY_TIME = os.getenv("DAILY_SUMMARY_TIME", "09:00")
APP_ENV = os.getenv("APP_ENV", "development")

# Dashboard settings
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5000"))
DASHBOARD_DEBUG = os.getenv("DASHBOARD_DEBUG", "True").lower() == "true"

# Admin credentials (basic auth support)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Security allowlists
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "")
WHATSAPP_ADMIN_ID = os.getenv("WHATSAPP_ADMIN_ID", "")
DASHBOARD_ADMIN_USER = os.getenv("DASHBOARD_ADMIN_USER", "admin")
DASHBOARD_ADMIN_PASS = os.getenv("DASHBOARD_ADMIN_PASS", "admin123")
