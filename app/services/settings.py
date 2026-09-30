from __future__ import annotations

DEFAULTS = {
    "subscription_enabled": "true",
    "subscription_channel_id": "",
    "subscription_channel_url": "",
    "target_channel_id": "",
    "target_channel_url": "",
    "reaction_enabled": "true",
    "reaction_emoji": "🔥",
    "post_header": "📚 KUNNING KITOB TAVSIYASI",
    "post_footer": "📖 Siz ham o‘qigan kitobingizni boshqalarga tavsiya qiling.\n👉 /start",
}


def setting_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
