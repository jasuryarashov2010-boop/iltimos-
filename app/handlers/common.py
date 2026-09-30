from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..keyboards import admin_keyboard, subscription_keyboard, user_keyboard
from ..repositories import Repository
from ..services.subscription import ensure_access, is_subscribed
from ..texts import AdminButtons, UserButtons, main_menu

router = Router(name="common")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, repo: Repository, settings):
    await state.clear()
    await repo.upsert_user(message.from_user)
    is_admin = message.from_user.id in settings.admin_ids
    if not is_admin and not await ensure_access(message, message.bot, repo, False):
        return
    await message.answer(main_menu(is_admin), reply_markup=admin_keyboard() if is_admin else user_keyboard())


@router.message(Command("cancel"))
@router.message(F.text == UserButtons.CANCEL)
async def cancel(message: Message, state: FSMContext, settings):
    await state.clear()
    is_admin = message.from_user.id in settings.admin_ids
    await message.answer("↩️ <b>Amal bekor qilindi.</b>", reply_markup=admin_keyboard() if is_admin else user_keyboard())


@router.message(F.text == UserButtons.HOME)
@router.message(F.text == AdminButtons.HOME)
async def home(message: Message, state: FSMContext, settings, repo: Repository):
    await state.clear()
    is_admin = message.from_user.id in settings.admin_ids
    await message.answer(main_menu(is_admin), reply_markup=admin_keyboard() if is_admin else user_keyboard())


@router.callback_query(F.data == "sub:check")
async def sub_check(call: CallbackQuery, repo: Repository, settings):
    if call.from_user.id in settings.admin_ids:
        await call.answer("✅ Admin uchun obuna shart emas.")
        return
    cfg = await repo.get_settings()
    status = await is_subscribed(call.bot, call.from_user.id, cfg.get("subscription_channel_id", ""))
    if status is True:
        await call.answer("✅ Obuna tasdiqlandi!")
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(main_menu(False), reply_markup=user_keyboard())
    elif status is False:
        await call.answer("❌ Kanalga hali obuna bo‘lmagansiz.", show_alert=True)
    else:
        await call.answer("⚠️ Tekshirishda xatolik. Kanal sozlamalarini tekshiring.", show_alert=True)
