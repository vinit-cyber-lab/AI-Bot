import discord
from typing import Optional

from config import DISCORD_BOT_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from services.whatsapp_service import send_whatsapp_message
import requests


class MessagingAdapter:
    @staticmethod
    def send_discord_dm(user_id: str, message: str) -> bool:
        if not DISCORD_BOT_TOKEN:
            return False
        headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}", "Content-Type": "application/json"}
        try:
            response = requests.post(
                "https://discord.com/api/v10/users/@me/channels",
                headers=headers,
                json={"recipient_id": str(user_id)},
                timeout=10,
            )
            if response.status_code not in (200, 201):
                return False
            channel = response.json()
            dm_response = requests.post(
                f"https://discord.com/api/v10/channels/{channel['id']}/messages",
                headers=headers,
                json={"content": message},
                timeout=10,
            )
            return dm_response.status_code in (200, 201)
        except Exception:
            return False

    @staticmethod
    def send_telegram_dm(chat_id: str, message: str) -> bool:
        if not TELEGRAM_BOT_TOKEN:
            return False
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": chat_id, "text": message, "disable_web_page_preview": True},
                timeout=10,
            )
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def send_whatsapp_dm(phone: str, message: str) -> bool:
        return send_whatsapp_message(message, phone)

    @classmethod
    def send_dm(cls, platform: str, target: str, message: str) -> bool:
        platform = (platform or "").lower().strip()
        if not target or not message:
            return False
        if platform == "discord":
            return cls.send_discord_dm(target, message)
        elif platform == "telegram":
            return cls.send_telegram_dm(target, message)
        elif platform == "whatsapp":
            return cls.send_whatsapp_dm(target, message)
        return False


class BroadcastAdapter:
    @staticmethod
    def broadcast_discord(message: str, webhook_url: str = "") -> bool:
        from config import DISCORD_WEBHOOK_URL
        url = webhook_url or DISCORD_WEBHOOK_URL
        if not url:
            return False
        try:
            requests.post(url, json={"content": message}, timeout=10)
            return True
        except Exception:
            return False

    @staticmethod
    def broadcast_telegram(message: str) -> bool:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            return False
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": message, "disable_web_page_preview": True},
                timeout=10,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def broadcast_whatsapp(message: str) -> bool:
        return send_whatsapp_message(message)

    @classmethod
    def broadcast(cls, message: str, channels: list = None) -> dict:
        channels = channels or ["discord", "telegram"]
        results = {}
        for channel in channels:
            if channel == "discord":
                results[channel] = cls.broadcast_discord(message)
            elif channel == "telegram":
                results[channel] = cls.broadcast_telegram(message)
            elif channel == "whatsapp":
                results[channel] = cls.broadcast_whatsapp(message)
        return results
