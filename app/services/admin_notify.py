from __future__ import annotations

import logging

from aiogram import Bot

from ..format_admin import recommendation_admin_text
from ..keyboards import admin_recommendation_keyboard
from ..repositories import Repository

logger = logging.getLogger(__name__)


async def notify_recommendation(bot: Bot, repo: Repository, admin_ids: set[int] | frozenset[int], rec_id: int) -> None:
    rec = await repo.get_recommendation(rec_id)
    if not rec:
        return
    text = recommendation_admin_text(rec)
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, text, reply_markup=admin_recommendation_keyboard(rec.id))
            if rec.photo_file_id:
                await bot.send_photo(admin_id, rec.photo_file_id, caption=f"🖼 #{rec.id} — kitob rasmi")
        except Exception:
            logger.exception("Could not notify admin %s about recommendation %s", admin_id, rec_id)
