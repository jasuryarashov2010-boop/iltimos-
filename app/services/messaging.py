from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

logger = logging.getLogger(__name__)


async def broadcast_text(bot: Bot, user_ids: list[int], text: str) -> tuple[int, int]:
    ok = 0
    failed = 0
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text)
            ok += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.04)
    return ok, failed
