import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN
from services.github_service import fetch_repo_summary
from services.system_service import get_system_status
from bot import backup_task

logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI-Bot is active.\n\n"
        "Available commands:\n"
        "/status\n"
        "/github\n"
        "/health\n"
        "/backup\n"
        "/logs\n"
        "/help"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ AI-Bot is running and monitoring tasks.")


async def github_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    repo = fetch_repo_summary("vinit-cyber-lab/AI-Bot")
    if not repo:
        await update.message.reply_text("❌ GitHub data is currently unavailable.")
        return

    text = (
        f"Repository: {repo.get('full_name', 'N/A')}\n"
        f"Stars: {repo.get('stargazers_count', 0)}\n"
        f"Forks: {repo.get('forks_count', 0)}\n"
        f"Open Issues: {repo.get('open_issues_count', 0)}\n"
        f"Last Push: {repo.get('pushed_at', 'N/A')}"
    )
    await update.message.reply_text(text)


async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_system_status()
    if not stats:
        await update.message.reply_text("❌ System health data is unavailable.")
        return

    text = (
        f"CPU: {stats.get('cpu_percent', 0)}%\n"
        f"Memory: {stats.get('memory_percent', 0)}%\n"
        f"Disk: {stats.get('disk_percent', 0)}%\n"
        f"Platform: {stats.get('platform', 'N/A')}"
    )
    await update.message.reply_text(text)


async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        backup_task()
        await update.message.reply_text("✅ Backup task triggered successfully.")
    except Exception as exc:
        await update.message.reply_text(f"❌ Backup failed: {exc}")


async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("logs/bot.log", "r", encoding="utf-8") as file:
            lines = file.readlines()[-20:]
        content = "".join(lines) or "No logs available yet."
        await update.message.reply_text(f"<pre>{content}</pre>", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("No logs found yet.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "/start\n"
        "/status\n"
        "/github\n"
        "/health\n"
        "/backup\n"
        "/logs\n"
        "/help"
    )


def run_telegram_bot():
    if not TELEGRAM_BOT_TOKEN:
        logging.warning("TELEGRAM_BOT_TOKEN is missing. Telegram control is disabled.")
        return

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("github", github_info))
    application.add_handler(CommandHandler("health", health))
    application.add_handler(CommandHandler("backup", backup))
    application.add_handler(CommandHandler("logs", logs))
    application.add_handler(CommandHandler("help", help_cmd))
    application.run_polling()


if __name__ == "__main__":
    run_telegram_bot()
