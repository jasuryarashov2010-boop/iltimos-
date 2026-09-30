from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..format_admin import recommendation_admin_text
from ..keyboards import (
    admin_keyboard,
    admin_recommendation_keyboard,
    broadcast_keyboard,
    channel_settings_keyboard,
    design_keyboard,
    reaction_keyboard,
    rec_edit_keyboard,
    user_result_keyboard,
)
from ..repositories import Repository
from ..services.messaging import broadcast_text
from ..services.publishing import publish_recommendation
from ..services.rendering import render_recommendation
from ..services.settings import DEFAULTS, setting_bool
from ..states import (
    BroadcastFlow,
    ChannelSettingFlow,
    DesignFlow,
    EditRecommendationFlow,
    ReactionFlow,
    RejectFlow,
    UserSearchFlow,
)
from ..texts import AdminButtons
from ..utils import html

router = Router(name="admin")
logger = logging.getLogger(__name__)


def _admin_denied() -> str:
    return "⛔ <b>Bu bo‘lim faqat adminlar uchun.</b>"


@router.message(F.text == AdminButtons.RECOMMENDATIONS)
async def admin_recommendations(message: Message, repo: Repository):
    items = await repo.list_pending_recommendations()
    if not items:
        await message.answer(
            "📭 <b>Kutilayotgan tavsiyalar yo‘q.</b>\n\n"
            "✅ Barcha tavsiyalar ko‘rib chiqilgan.",
            reply_markup=admin_keyboard(),
        )
        return

    await message.answer(
        f"📥 <b>Kutilayotgan tavsiyalar: {len(items)}</b>\n\n"
        "Har bir tavsiyani preview qilib, keyin joylang yoki rad eting.",
        reply_markup=admin_keyboard(),
    )
    for rec in items:
        await message.answer(
            recommendation_admin_text(rec),
            reply_markup=admin_recommendation_keyboard(rec.id),
        )
        if rec.photo_file_id:
            await message.bot.send_photo(
                message.chat.id,
                rec.photo_file_id,
                caption=f"🖼 <b>#{rec.id}</b> — kitob rasmi",
            )


@router.callback_query(F.data.startswith("admrec:preview:"))
async def admin_preview(call: CallbackQuery, repo: Repository):
    rec_id = int(call.data.rsplit(":", 1)[1])
    rec = await repo.get_recommendation(rec_id)
    if rec is None:
        await call.answer("❌ Tavsiya topilmadi.", show_alert=True)
        return

    settings = await repo.get_settings()
    text = render_recommendation(
        rec.title,
        rec.author,
        rec.review,
        settings.get("post_header", ""),
        settings.get("post_footer", ""),
    )
    if rec.photo_file_id:
        await call.message.answer_photo(rec.photo_file_id, caption=text)
    else:
        await call.message.answer(text)
    await call.answer("👀 Preview yuborildi")


@router.callback_query(F.data.startswith("admrec:publish:"))
async def admin_publish(call: CallbackQuery, repo: Repository):
    rec_id = int(call.data.rsplit(":", 1)[1])
    await call.answer("⏳ Joylanmoqda…")
    ok, msg = await publish_recommendation(call.bot, repo, rec_id)
    await call.message.answer(msg, reply_markup=admin_keyboard())
    if ok:
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception:
            logger.debug("Could not remove moderation keyboard", exc_info=True)


@router.callback_query(F.data.startswith("admrec:reject:"))
async def admin_reject(call: CallbackQuery, state: FSMContext):
    rec_id = int(call.data.rsplit(":", 1)[1])
    await state.clear()
    await state.set_state(RejectFlow.reason)
    await state.update_data(rec_id=rec_id)
    await call.message.answer(
        f"❌ <b>#{rec_id}</b> uchun rad etish sababini yozing.\n\n"
        "Masalan: ma’lumotlar yetarli emas yoki kitob avval joylangan.",
        reply_markup=admin_keyboard(),
    )
    await call.answer()


@router.message(RejectFlow.reason)
async def admin_reject_reason(message: Message, state: FSMContext, repo: Repository):
    reason = (message.text or "").strip()
    if len(reason) < 3:
        await message.answer(
            "⚠️ <b>Sabab juda qisqa.</b> Kamida 3 belgi yozing.",
            reply_markup=admin_keyboard(),
        )
        return

    data = await state.get_data()
    rec_id = int(data["rec_id"])
    user_id = await repo.reject_recommendation(rec_id, reason)
    await state.clear()

    if user_id is None:
        await message.answer(
            "⚠️ Tavsiya allaqachon qayta ishlangan.",
            reply_markup=admin_keyboard(),
        )
        return

    try:
        await message.bot.send_message(
            user_id,
            f"🔴 <b>Tavsiyangiz #{rec_id} rad etildi.</b>\n\n"
            f"📝 <b>Sabab:</b> {html(reason)}",
        )
    except Exception:
        logger.warning("Could not notify user %s about rejection", user_id, exc_info=True)

    await message.answer(
        f"✅ <b>#{rec_id}</b> rad etildi.",
        reply_markup=admin_keyboard(),
    )


@router.callback_query(F.data.startswith("admrec:edit:"))
async def admin_edit(call: CallbackQuery):
    rec_id = int(call.data.rsplit(":", 1)[1])
    await call.message.answer(
        f"✏️ <b>#{rec_id}</b> — qaysi maydonni o‘zgartirasiz?",
        reply_markup=rec_edit_keyboard(rec_id),
    )
    await call.answer()


@router.callback_query(F.data.startswith("recedit:"))
async def edit_field(call: CallbackQuery, state: FSMContext):
    _, field, rec_id = call.data.split(":")
    labels = {
        "title": "📖 yangi kitob nomini",
        "author": "✍️ yangi muallifni",
        "review": "💭 yangi fikrni",
    }
    if field not in labels:
        await call.answer("⚠️ Noma’lum maydon.", show_alert=True)
        return

    await state.clear()
    await state.set_state(EditRecommendationFlow.value)
    await state.update_data(field=field, rec_id=int(rec_id))
    await call.message.answer(
        f"✏️ {labels[field]} yuboring:",
        reply_markup=admin_keyboard(),
    )
    await call.answer()


@router.message(EditRecommendationFlow.value)
async def edit_value(message: Message, state: FSMContext, repo: Repository):
    value = (message.text or "").strip()
    data = await state.get_data()
    field = data.get("field")
    rec_id = int(data.get("rec_id", 0))

    limits = {"title": 300, "author": 300, "review": 5000}
    limit = limits.get(field, 0)
    if not field or rec_id <= 0 or not limit:
        await state.clear()
        await message.answer("⚠️ Tahrirlash sessiyasi eskirgan.", reply_markup=admin_keyboard())
        return
    if not value or len(value) > limit:
        await message.answer(
            f"⚠️ Matn {limit} belgidan oshmasin. Qaytadan yuboring.",
            reply_markup=admin_keyboard(),
        )
        return

    ok = await repo.edit_recommendation(rec_id, field, value)
    await state.clear()
    await message.answer(
        "✅ O‘zgartirish saqlandi." if ok else "⚠️ Tavsiya tahrirlanmadi.",
        reply_markup=admin_keyboard(),
    )


@router.message(F.text == AdminButtons.DESIGN)
async def design_menu(message: Message, repo: Repository):
    s = await repo.get_settings()
    text = (
        "<b>🎨 POST DIZAYNI</b>\n\n"
        "🪧 <b>Header:</b>\n"
        f"<code>{html(s.get('post_header', ''))}</code>\n\n"
        "🔚 <b>Footer / CTA:</b>\n"
        f"<code>{html(s.get('post_footer', ''))}</code>"
    )
    await message.answer(text, reply_markup=design_keyboard())


@router.callback_query(F.data == "design:header")
async def design_header(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(DesignFlow.header)
    await call.message.answer(
        "🪧 <b>Yangi header</b>ni yuboring.\n\n"
        "120 belgigacha bo‘lishi mumkin.",
        reply_markup=admin_keyboard(),
    )
    await call.answer()


@router.message(DesignFlow.header)
async def design_header_save(message: Message, state: FSMContext, repo: Repository):
    value = (message.text or "").strip()
    if not value:
        await message.answer("⚠️ Header bo‘sh bo‘lmasin.", reply_markup=admin_keyboard())
        return
    await repo.set_setting("post_header", value[:120])
    await state.clear()
    await message.answer("✅ Header saqlandi.", reply_markup=admin_keyboard())


@router.callback_query(F.data == "design:footer")
async def design_footer(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(DesignFlow.footer)
    await call.message.answer(
        "🔚 <b>Yangi footer / CTA</b>ni yuboring.\n\n"
        "500 belgigacha bo‘lishi mumkin.",
        reply_markup=admin_keyboard(),
    )
    await call.answer()


@router.message(DesignFlow.footer)
async def design_footer_save(message: Message, state: FSMContext, repo: Repository):
    value = (message.text or "").strip()
    if not value:
        await message.answer("⚠️ Footer bo‘sh bo‘lmasin.", reply_markup=admin_keyboard())
        return
    await repo.set_setting("post_footer", value[:500])
    await state.clear()
    await message.answer("✅ Footer saqlandi.", reply_markup=admin_keyboard())


@router.callback_query(F.data == "design:reset")
async def design_reset(call: CallbackQuery, repo: Repository):
    await repo.set_setting("post_header", DEFAULTS["post_header"])
    await repo.set_setting("post_footer", DEFAULTS["post_footer"])
    await call.answer("↩️ Standart dizayn tiklandi.")


@router.message(F.text == AdminButtons.REACTION)
async def reaction_menu(message: Message, repo: Repository):
    settings_row = await repo.get_settings()
    enabled = setting_bool(settings_row.get("reaction_enabled"), True)
    emoji = settings_row.get("reaction_emoji", "🔥")
    await message.answer(
        "<b>🔥 REAKSIYA SOZLAMALARI</b>\n\n"
        f"Holat: {'✅ Faol' if enabled else '❌ O‘chiq'}\n"
        f"Emoji: {html(emoji)}\n\n"
        "💡 Admin emoji'ni o‘zi yuboradi.",
        reply_markup=reaction_keyboard(enabled),
    )


@router.callback_query(F.data == "reaction:set")
async def reaction_set(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ReactionFlow.emoji)
    await call.message.answer(
        "🔥 Kanal postlariga qo‘yiladigan reaction emoji'ni yuboring.\n\n"
        "Masalan: <code>🔥</code> yoki <code>❤️</code>",
        reply_markup=admin_keyboard(),
    )
    await call.answer()


@router.message(ReactionFlow.emoji)
async def reaction_save(message: Message, state: FSMContext, repo: Repository):
    emoji = (message.text or "").strip()
    if not emoji or len(emoji) > 16 or any(ch.isalnum() for ch in emoji):
        await message.answer(
            "⚠️ Faqat emoji reaction yuboring. Masalan: <code>🔥</code>",
            reply_markup=admin_keyboard(),
        )
        return
    await repo.set_setting("reaction_emoji", emoji)
    await state.clear()
    await message.answer(f"✅ Yangi reaction: {html(emoji)}", reply_markup=admin_keyboard())


@router.callback_query(F.data == "reaction:toggle")
async def reaction_toggle(call: CallbackQuery, repo: Repository):
    current = setting_bool(await repo.get_setting("reaction_enabled", "true"), True)
    await repo.set_setting("reaction_enabled", "false" if current else "true")
    await call.answer("✅ Reaction holati yangilandi.")


@router.message(F.text == AdminButtons.CHANNEL)
async def channel_menu(message: Message, repo: Repository):
    s = await repo.get_settings()
    text = (
        "<b>📢 KANAL SOZLAMALARI</b>\n\n"
        f"🎯 <b>Post ID:</b> <code>{html(s.get('target_channel_id', '—'))}</code>\n"
        f"🔗 <b>Post URL:</b> {html(s.get('target_channel_url', '—'))}\n\n"
        f"🔐 <b>Obuna:</b> {'✅' if setting_bool(s.get('subscription_enabled'), True) else '❌'}\n"
        f"🔐 <b>Obuna ID:</b> <code>{html(s.get('subscription_channel_id', '—'))}</code>\n"
        f"🔗 <b>Obuna URL:</b> {html(s.get('subscription_channel_url', '—'))}"
    )
    await message.answer(text, reply_markup=channel_settings_keyboard())


@router.callback_query(F.data == "channel:target_id")
async def target_id(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ChannelSettingFlow.target_id)
    await call.message.answer(
        "🎯 <b>Post kanalingizning numeric ID'sini yuboring.</b>\n\n"
        "Masalan: <code>-1001234567890</code>",
        reply_markup=admin_keyboard(),
    )
    await call.answer()


@router.message(ChannelSettingFlow.target_id)
async def target_id_save(message: Message, state: FSMContext, repo: Repository):
    value = (message.text or "").strip()
    try:
        int(value)
    except ValueError:
        await message.answer("⚠️ Numeric channel ID yuboring.", reply_markup=admin_keyboard())
        return
    await repo.set_setting("target_channel_id", value)
    await state.clear()
    await message.answer("✅ Post kanali ID saqlandi.", reply_markup=admin_keyboard())


@router.callback_query(F.data == "channel:target_url")
async def target_url(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ChannelSettingFlow.target_url)
    await call.message.answer(
        "🔗 <b>Post kanal URL'ini yuboring.</b>\n\n"
        "Masalan: https://t.me/mazmunda",
        reply_markup=admin_keyboard(),
    )
    await call.answer()


@router.message(ChannelSettingFlow.target_url)
async def target_url_save(message: Message, state: FSMContext, repo: Repository):
    value = (message.text or "").strip()
    if not value.startswith(("https://t.me/", "http://t.me/", "https://telegram.me/")):
        await message.answer("⚠️ Telegram kanal URL'ini yuboring.", reply_markup=admin_keyboard())
        return
    await repo.set_setting("target_channel_url", value[:500])
    await state.clear()
    await message.answer("✅ Post kanal URL saqlandi.", reply_markup=admin_keyboard())


@router.callback_query(F.data == "channel:sub_id")
async def sub_id(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ChannelSettingFlow.subscription_id)
    await call.message.answer(
        "🔐 <b>Majburiy obuna kanalining numeric ID'sini yuboring.</b>",
        reply_markup=admin_keyboard(),
    )
    await call.answer()


@router.message(ChannelSettingFlow.subscription_id)
async def sub_id_save(message: Message, state: FSMContext, repo: Repository):
    value = (message.text or "").strip()
    try:
        int(value)
    except ValueError:
        await message.answer("⚠️ Numeric channel ID yuboring.", reply_markup=admin_keyboard())
        return
    await repo.set_setting("subscription_channel_id", value)
    await state.clear()
    await message.answer("✅ Obuna kanali ID saqlandi.", reply_markup=admin_keyboard())


@router.callback_query(F.data == "channel:sub_url")
async def sub_url(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ChannelSettingFlow.subscription_url)
    await call.message.answer(
        "🔗 <b>Majburiy obuna kanalining URL'ini yuboring.</b>",
        reply_markup=admin_keyboard(),
    )
    await call.answer()


@router.message(ChannelSettingFlow.subscription_url)
async def sub_url_save(message: Message, state: FSMContext, repo: Repository):
    value = (message.text or "").strip()
    if not value.startswith(("https://t.me/", "http://t.me/", "https://telegram.me/")):
        await message.answer("⚠️ Telegram kanal URL'ini yuboring.", reply_markup=admin_keyboard())
        return
    await repo.set_setting("subscription_channel_url", value[:500])
    await state.clear()
    await message.answer("✅ Obuna kanali URL saqlandi.", reply_markup=admin_keyboard())


@router.callback_query(F.data == "channel:sub_toggle")
async def sub_toggle(call: CallbackQuery, repo: Repository):
    current = setting_bool(await repo.get_setting("subscription_enabled", "true"), True)
    await repo.set_setting("subscription_enabled", "false" if current else "true")
    await call.answer("✅ Majburiy obuna holati yangilandi.")


@router.message(F.text == AdminButtons.USERS)
async def users_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserSearchFlow.query)
    await message.answer(
        "🔎 <b>Foydalanuvchi qidiring.</b>\n\n"
        "ID, username yoki ism yuboring.",
        reply_markup=admin_keyboard(),
    )


@router.message(UserSearchFlow.query)
async def user_search(message: Message, state: FSMContext, repo: Repository):
    query = (message.text or "").strip()
    items = await repo.search_users(query)
    await state.clear()
    if not items:
        await message.answer("🔎 <b>Foydalanuvchi topilmadi.</b>", reply_markup=admin_keyboard())
        return
    for user in items:
        username = f"@{html(user.username)}" if user.username else "—"
        text = (
            "👤 <b>FOYDALANUVCHI</b>\n\n"
            f"🆔 <code>{user.id}</code>\n"
            f"👤 {username}\n"
            f"📝 {html(user.first_name or '')}\n"
            f"🚫 Blok: {'✅' if user.is_blocked else '❌'}"
        )
        await message.answer(text, reply_markup=user_result_keyboard(user.id, user.is_blocked))


@router.callback_query(F.data.startswith("user:"))
async def user_action(call: CallbackQuery, repo: Repository):
    _, action, user_id_raw = call.data.split(":")
    user_id = int(user_id_raw)
    blocked = action == "block"
    await repo.set_blocked(user_id, blocked)
    await call.message.edit_reply_markup(reply_markup=user_result_keyboard(user_id, blocked))
    await call.answer("✅ Foydalanuvchi holati yangilandi.")


@router.message(F.text == AdminButtons.BROADCAST)
async def broadcast_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(BroadcastFlow.text)
    await message.answer(
        "📣 <b>Barchaga yuboriladigan xabarni yozing.</b>\n\n"
        "Keyin preview ko‘rasiz.",
        reply_markup=admin_keyboard(),
    )


@router.message(BroadcastFlow.text)
async def broadcast_preview(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer("⚠️ Xabar juda qisqa.", reply_markup=admin_keyboard())
        return
    await state.update_data(text=text)
    await message.answer(
        "<b>👀 BROADCAST PREVIEW</b>\n\n" + html(text),
        reply_markup=broadcast_keyboard(),
    )


@router.callback_query(F.data == "broadcast:send")
async def broadcast_send(call: CallbackQuery, state: FSMContext, repo: Repository):
    data = await state.get_data()
    text = data.get("text", "")
    if not text:
        await state.clear()
        await call.answer("⚠️ Broadcast sessiyasi eskirgan.", show_alert=True)
        return
    await state.clear()
    ids = await repo.broadcast_users()
    ok, failed = await broadcast_text(call.bot, ids, html(text))
    await call.message.answer(
        "📣 <b>Broadcast yakunlandi.</b>\n\n"
        f"✅ Yuborildi: {ok}\n"
        f"❌ Yetkazilmadi: {failed}",
        reply_markup=admin_keyboard(),
    )
    await call.answer()


@router.callback_query(F.data == "broadcast:cancel")
async def broadcast_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("↩️ Broadcast bekor qilindi.", reply_markup=admin_keyboard())
    await call.answer()


@router.message(F.text == AdminButtons.STATS)
async def stats(message: Message, repo: Repository):
    stats_data = await repo.stats()
    text = (
        "<b>📊 STATISTIKA</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{stats_data['users']}</b>\n"
        f"📥 Kutilmoqda: <b>{stats_data['pending']}</b>\n"
        f"🟢 Kanalga joylangan: <b>{stats_data['published']}</b>\n"
        f"🔴 Rad etilgan: <b>{stats_data['rejected']}</b>\n"
        f"📨 Ochiq murojaatlar: <b>{stats_data['tickets']}</b>"
    )
    await message.answer(text, reply_markup=admin_keyboard())


@router.message(F.text == AdminButtons.SYSTEM)
async def system_status(message: Message, repo: Repository, storage_bundle, bot):
    db_ok = await repo.db.ping()
    redis_ok = await storage_bundle.ping()
    try:
        me = await bot.get_me()
        bot_ok = bool(me)
    except Exception:
        bot_ok = False
    text = (
        "<b>⚙️ TIZIM HOLATI</b>\n\n"
        f"🤖 Telegram API: {'🟢' if bot_ok else '🔴'}\n"
        f"🗄 PostgreSQL: {'🟢' if db_ok else '🔴'}\n"
        f"🧠 Redis: {'🟢' if redis_ok else '🟡 Fallback/yo‘q'}"
    )
    await message.answer(text, reply_markup=admin_keyboard())
