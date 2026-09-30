from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import ReactionTypeEmoji

from ..repositories import Repository

logger = logging.getLogger(__name__)


async def react_to_message(bot: Bot, repo: Repository, chat_id: int | str, message_id: int) -> bool:
    settings = await repo.get_settings()
    if settings.get("reaction_enabled", "true").lower() != "true":
        return False
    emoji = (settings.get("reaction_emoji") or "🔥").strip()
    if not emoji:
        return False
    try:
        await bot.set_message_reaction(
            chat_id=chat_id,
            message_id=message_id,
            reaction=[ReactionTypeEmoji(emoji=emoji)],
            is_big=False,
        )
        return True
    except Exception as exc:
        logger.warning("Could not set reaction %r on %s/%s: %s", emoji, chat_id, message_id, exc)
        return False
