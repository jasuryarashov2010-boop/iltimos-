from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import FSInputFile

from ..repositories import Repository
from .reactions import react_to_message
from .rendering import render_recommendation

logger = logging.getLogger(__name__)


async def publish_recommendation(bot: Bot, repo: Repository, rec_id: int) -> tuple[bool, str]:
    rec = await repo.get_recommendation(rec_id)
    if rec is None:
        return False, "Tavsiya topilmadi."
    if not await repo.claim_recommendation(rec_id):
        return False, "Bu tavsiya allaqachon boshqa admin tomonidan qayta ishlanmoqda yoki yakunlangan."
    settings = await repo.get_settings()
    target_raw = settings.get("target_channel_id", "").strip()
    target = int(target_raw) if target_raw.lstrip("-").isdigit() else target_raw
    if not target:
        await repo.return_to_pending(rec_id)
        return False, "Post kanali hali sozlanmagan."
    header = settings.get("post_header", "")
    footer = settings.get("post_footer", "")
    text = render_recommendation(rec.title, rec.author, rec.review, header, footer)
    try:
        if rec.photo_file_id:
            sent = await bot.send_photo(chat_id=target, photo=rec.photo_file_id, caption=text)
        else:
            sent = await bot.send_message(chat_id=target, text=text)
        await repo.mark_published(rec_id, sent.message_id)
        await react_to_message(bot, repo, target, sent.message_id)
        return True, "✅ Tavsiya kanalga muvaffaqiyatli joylandi."
    except Exception:
        logger.exception("Publish failed for recommendation %s", rec_id)
        await repo.return_to_pending(rec_id)
        return False, "❌ Kanalga joylashda xatolik yuz berdi. Tavsiya qayta navbatga qaytarildi."
