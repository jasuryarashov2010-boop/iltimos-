from __future__ import annotations

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, Message
from aiogram.enums import ChatMemberStatus

from ..keyboards import subscription_keyboard
from ..repositories import Repository
from ..texts import subscription_text


def bool_value(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


async def is_subscribed(bot: Bot, user_id: int, channel_id: str) -> bool | None:
    if not channel_id:
        return True
    try:
        member = await bot.get_chat_member(chat_id=int(channel_id), user_id=user_id)
        return member.status in {
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        } or (member.status == ChatMemberStatus.RESTRICTED and bool(member.is_member))
    except Exception:
        return None


async def ensure_access(message: Message, bot: Bot, repo: Repository, is_admin: bool) -> bool:
    if is_admin:
        return True
    settings = await repo.get_settings()
    if not bool_value(settings.get("subscription_enabled"), True):
        return True
    channel_id = settings.get("subscription_channel_id", "").strip()
    channel_url = settings.get("subscription_channel_url", "").strip()
    if not channel_id or not channel_url:
        # Fail open rather than breaking /start when admin has not configured a channel yet.
        return True
    status = await is_subscribed(bot, message.from_user.id, channel_id)
    if status is True:
        return True
    await message.answer(subscription_text(), reply_markup=subscription_keyboard(channel_url))
    return False
