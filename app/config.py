from __future__ import annotations

import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse


SECRET_RE = re.compile(r"^[A-Za-z0-9_-]{1,256}$")


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def normalize_db_url(value: str | None) -> str:
    value = (value or "").strip()
    if not value:
        return "sqlite+aiosqlite:///./local.db"
    if value.startswith("postgres://"):
        return "postgresql+asyncpg://" + value[len("postgres://") :]
    if value.startswith("postgresql://"):
        return "postgresql+asyncpg://" + value[len("postgresql://") :]
    return value


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]
    bot_username: str
    database_url: str
    redis_url: str | None
    webhook_base_url: str | None
    webhook_path: str
    webhook_secret: str | None
    log_level: str
    subscription_enabled_default: bool
    max_review_length: int

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("BOT_TOKEN is required")

        raw_admins = os.getenv("ADMIN_IDS", "")
        ids = set()
        for part in raw_admins.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                ids.add(int(part))
            except ValueError as exc:
                raise RuntimeError("ADMIN_IDS must contain numeric Telegram IDs") from exc
        if len(ids) != 2:
            raise RuntimeError("ADMIN_IDS must contain exactly 2 unique Telegram IDs")

        secret = os.getenv("WEBHOOK_SECRET", "").strip() or None
        if secret and not SECRET_RE.fullmatch(secret):
            raise RuntimeError("WEBHOOK_SECRET may contain only A-Z, a-z, 0-9, _ and -")

        base = os.getenv("WEBHOOK_BASE_URL", "").strip() or os.getenv("RENDER_EXTERNAL_URL", "").strip() or None
        if base:
            base = base.rstrip("/")
            parsed = urlparse(base)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise RuntimeError("WEBHOOK_BASE_URL must be a valid http(s) URL")

        return cls(
            bot_token=token,
            admin_ids=frozenset(ids),
            bot_username=os.getenv("BOT_USERNAME", "").strip().lstrip("@"),
            database_url=normalize_db_url(os.getenv("DATABASE_URL")),
            redis_url=os.getenv("REDIS_URL", "").strip() or None,
            webhook_base_url=base,
            webhook_path=os.getenv("WEBHOOK_PATH", "/telegram/webhook").strip() or "/telegram/webhook",
            webhook_secret=secret,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            subscription_enabled_default=env_bool("FORCE_SUBSCRIPTION", True),
            max_review_length=max(100, int(os.getenv("MAX_REVIEW_LENGTH", "1200"))),
        )
