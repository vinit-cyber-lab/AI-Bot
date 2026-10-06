import json

import requests

from config import DISCORD_WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_discord(message: str) -> bool:
    if not DISCORD_WEBHOOK_URL:
        return False
    try:
        payload = {"content": message}
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        return response.status_code in (200, 204)
    except Exception:
        return False


def send_telegram(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True,
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def send_all(message: str):
    delivered = False
    if send_discord(message):
        delivered = True
    if send_telegram(message):
        delivered = True

    if not delivered:
        print(f"[notifications] No active channel configured. Message not sent: {message}")
