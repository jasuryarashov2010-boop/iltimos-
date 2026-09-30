from __future__ import annotations

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from .repositories import Repository
from .services.subscription import ensure_access


class RegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        repo: Repository = data["repo"]
        user = getattr(event, "from_user", None)
        if user:
            db_user = await repo.upsert_user(user)
            data["db_user"] = db_user
        return await handler(event, data)


class UserAccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        settings = data["settings"]
        repo: Repository = data["repo"]
        if not user:
            return await handler(event, data)
        if user.id in settings.admin_ids:
            return await handler(event, data)
        if isinstance(event, Message) and (event.text or "").startswith("/start"):
            return await handler(event, data)
        if isinstance(event, CallbackQuery) and event.data == "sub:check":
            return await handler(event, data)
        ok = await ensure_access(event, data["bot"], repo, False) if isinstance(event, Message) else True
        if not ok:
            if isinstance(event, CallbackQuery):
                await event.answer("🔐 Avval kanalga obuna bo‘ling.", show_alert=True)
            return None
        return await handler(event, data)


class AdminOnlyMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        settings = data["settings"]
        if not user or user.id not in settings.admin_ids:
            if hasattr(event, "answer"):
                try:
                    await event.answer("🚫 Bu bo‘lim faqat adminlar uchun.", show_alert=True)
                except TypeError:
                    await event.answer("🚫 Bu bo‘lim faqat adminlar uchun.")
            return None
        return await handler(event, data)
