from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from fastapi import FastAPI, Header, HTTPException

from .config import Settings
from .db import Database
from .handlers import admin, channel, common, support, user
from .logging_setup import setup_logging
from .middlewares import AdminOnlyMiddleware, RegistrationMiddleware, UserAccessMiddleware
from .repositories import Repository
from .redis_store import StorageBundle
from .services.settings import DEFAULTS

settings = Settings.from_env()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

db = Database(settings.database_url)
storage_bundle = StorageBundle(settings.redis_url)
bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=storage_bundle.storage)
repo = Repository(db)

dp["settings"] = settings
dp["repo"] = repo
dp["storage_bundle"] = storage_bundle

dp.include_router(common.router)
user.router.message.middleware(RegistrationMiddleware())
user.router.callback_query.middleware(RegistrationMiddleware())
user.router.message.middleware(UserAccessMiddleware())
user.router.callback_query.middleware(UserAccessMiddleware())
dp.include_router(user.router)

dp.include_router(support.router)
admin.router.message.middleware(RegistrationMiddleware())
admin.router.callback_query.middleware(RegistrationMiddleware())
admin.router.message.middleware(AdminOnlyMiddleware())
admin.router.callback_query.middleware(AdminOnlyMiddleware())
dp.include_router(admin.router)
dp.include_router(channel.router)

app = FastAPI(title="Kitobxon V10", version="10.0.0")


@app.api_route("/health", methods=["GET", "HEAD"])
async def health() -> dict:
    return {
        "status": "ok",
        "database": await db.ping(),
        "redis": await storage_bundle.ping(),
    }

@app.get("/ready")
async def ready() -> dict:
    if not await db.ping():
        raise HTTPException(status_code=503, detail="database_unavailable")
    return {"status": "ready"}


@app.post(settings.webhook_path)
async def telegram_webhook(payload: dict, x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    if settings.webhook_secret and x_telegram_bot_api_secret_token != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="invalid_webhook_secret")
    from aiogram.types import Update
    update = Update.model_validate(payload)
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.on_event("startup")
async def startup() -> None:
    await repo.ensure_defaults(DEFAULTS)
    await repo.recover_stuck_publishing()
    if settings.webhook_base_url:
        webhook_url = settings.webhook_base_url + settings.webhook_path
        await bot.set_webhook(
            webhook_url,
            secret_token=settings.webhook_secret,
            allowed_updates=["message", "callback_query", "channel_post", "edited_channel_post"],
            drop_pending_updates=False,
        )
        logger.info("Webhook configured: %s", webhook_url)
    else:
        logger.warning("WEBHOOK_BASE_URL/RENDER_EXTERNAL_URL is not available; bot API webhook is not configured")


@app.on_event("shutdown")
async def shutdown() -> None:
    await db.close()
    await storage_bundle.close()
    await bot.session.close()
