from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..keyboards import admin_keyboard, ticket_keyboard, user_keyboard
from ..repositories import Repository
from ..states import SupportFlow, SupportReplyFlow
from ..texts import AdminButtons, UserButtons
from ..utils import html
from ..services.subscription import ensure_access

router = Router(name="support")


@router.message(F.text == UserButtons.SUPPORT)
async def support_start(message: Message, state: FSMContext, repo: Repository, settings):
    if not await ensure_access(message, message.bot, repo, message.from_user.id in settings.admin_ids):
        return
    await state.set_state(SupportFlow.message)
    await message.answer(
        "💬 <b>Adminga xabaringizni yozing.</b>\n\n"
        "<i>Savol yoki muammoingizni batafsil yozing.</i>",
        reply_markup=user_keyboard(True),
    )


@router.message(SupportFlow.message)
async def support_save(message: Message, state: FSMContext, repo: Repository, settings):
    if not await ensure_access(message, message.bot, repo, message.from_user.id in settings.admin_ids):
        await state.clear()
        return
    text = (message.text or "").strip()
    if len(text) < 3:
        await message.answer("⚠️ Xabar juda qisqa. Qaytadan yozing.", reply_markup=user_keyboard(True))
        return
    ticket = await repo.create_ticket(message.from_user.id, text)
    await state.clear()
    await message.answer(f"✅ Murojaat #{ticket.id} yuborildi.\n📨 Admin javobini kuting.", reply_markup=user_keyboard())
    for admin_id in settings.admin_ids:
        await message.bot.send_message(
            admin_id,
            f"<b>📨 YANGI MUROJAAT #{ticket.id}</b>\n\n👤 <code>{message.from_user.id}</code>\n\n💬 {html(text)}",
            reply_markup=ticket_keyboard(ticket.id, "open"),
        )


@router.message(F.text == AdminButtons.TICKETS)
async def tickets(message: Message, repo: Repository, settings):
    if message.from_user.id not in settings.admin_ids:
        return
    items = await repo.open_tickets()
    if not items:
        await message.answer("📭 Ochiq murojaatlar yo‘q.", reply_markup=admin_keyboard())
        return
    await message.answer(f"📨 <b>Ochiq murojaatlar: {len(items)}</b>", reply_markup=admin_keyboard())
    for t in items:
        await message.answer(
            f"<b>📨 MUROJAAT #{t.id}</b>\n\n👤 <code>{t.user_id}</code>\n\n💬 {html(t.message_text)}",
            reply_markup=ticket_keyboard(t.id, t.status),
        )


@router.callback_query(F.data.startswith("ticket:reply:"))
async def ticket_reply_start(call: CallbackQuery, state: FSMContext, settings):
    if call.from_user.id not in settings.admin_ids:
        await call.answer("⛔ Ruxsat yo‘q.", show_alert=True)
        return
    ticket_id = int(call.data.rsplit(":", 1)[1])
    await state.set_state(SupportReplyFlow.reply)
    await state.update_data(ticket_id=ticket_id)
    await call.message.answer(f"↩️ <b>#{ticket_id}</b> uchun javobni yozing:", reply_markup=admin_keyboard())
    await call.answer()


@router.message(SupportReplyFlow.reply)
async def ticket_reply_save(message: Message, state: FSMContext, repo: Repository, settings):
    if message.from_user.id not in settings.admin_ids:
        await state.clear()
        return
    data = await state.get_data()
    ticket_id = int(data["ticket_id"])
    reply = (message.text or "").strip()
    if len(reply) < 2:
        await message.answer("⚠️ Javob juda qisqa.", reply_markup=admin_keyboard())
        return
    user_id = await repo.reply_ticket(ticket_id, message.from_user.id, reply)
    await state.clear()
    if user_id:
        try:
            await message.bot.send_message(user_id, f"📨 <b>Admin javobi — #{ticket_id}</b>\n\n{html(reply)}")
        except Exception:
            pass
    await message.answer("✅ Javob yuborildi va murojaat yopildi.", reply_markup=admin_keyboard())


@router.callback_query(F.data.startswith("ticket:close:"))
async def ticket_close(call: CallbackQuery, repo: Repository, settings):
    if call.from_user.id not in settings.admin_ids:
        await call.answer("⛔ Ruxsat yo‘q.", show_alert=True)
        return
    ticket_id = int(call.data.rsplit(":", 1)[1])
    await repo.close_ticket(ticket_id)
    await call.message.edit_reply_markup(reply_markup=ticket_keyboard(ticket_id, "closed"))
    await call.answer("✅ Yopildi")


@router.callback_query(F.data.startswith("ticket:reopen:"))
async def ticket_reopen(call: CallbackQuery, repo: Repository, settings):
    if call.from_user.id not in settings.admin_ids:
        await call.answer("⛔ Ruxsat yo‘q.", show_alert=True)
        return
    ticket_id = int(call.data.rsplit(":", 1)[1])
    await repo.reopen_ticket(ticket_id)
    await call.message.edit_reply_markup(reply_markup=ticket_keyboard(ticket_id, "open"))
    await call.answer("↩️ Qayta ochildi")
