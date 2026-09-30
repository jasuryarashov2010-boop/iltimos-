from __future__ import annotations

from aiogram import Router
from aiogram.types import Message

from ..repositories import Repository
from ..services.reactions import react_to_message

router = Router(name="channel")


@router.channel_post()
async def on_channel_post(message: Message, repo: Repository):
    await react_to_message(message.bot, repo, message.chat.id, message.message_id)
