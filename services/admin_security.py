import os

TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "")
WHATSAPP_ADMIN_ID = os.getenv("WHATSAPP_ADMIN_ID", "")
DASHBOARD_ADMIN_USER = os.getenv("DASHBOARD_ADMIN_USER", "admin")
DASHBOARD_ADMIN_PASS = os.getenv("DASHBOARD_ADMIN_PASS", "admin123")


def _normalize_list(value: str):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


AUTHORIZED_TELEGRAM_IDS = _normalize_list(TELEGRAM_ADMIN_ID)
AUTHORIZED_WHATSAPP_IDS = _normalize_list(WHATSAPP_ADMIN_ID)


def is_authorized(source: str, user_id: str) -> bool:
    if not user_id:
        return False

    normalized = user_id.strip()
    source = (source or "").lower()

    if source == "telegram":
        return normalized in AUTHORIZED_TELEGRAM_IDS

    if source == "whatsapp":
        if normalized.startswith("whatsapp:"):
            normalized = normalized.replace("whatsapp:", "", 1)
        return normalized in AUTHORIZED_WHATSAPP_IDS

    return False
