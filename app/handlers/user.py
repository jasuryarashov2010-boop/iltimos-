from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..keyboards import recommendation_preview_keyboard, user_keyboard
from ..repositories import Repository
from ..services.admin_notify import notify_recommendation
from ..states import RecommendationFlow
from ..texts import UserButtons, status_label, rules_text
from ..utils import html

router = Router(name="user")


def draft_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Kitob nomi", callback_data="draftedit:title"),
         InlineKeyboardButton(text="✍️ Muallif", callback_data="draftedit:author")],
        [InlineKeyboardButton(text="💭 Fikr", callback_data="draftedit:review")],
        [InlineKeyboardButton(text="✅ Yuborish", callback_data="draftedit:done")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="rec:cancel")],
    ])


async def _next_prompt(message: Message, state: FSMContext, text: str) -> None:
    data = await state.get_data()
    old_id = data.get("prompt_id")
    if old_id:
        try:
            await message.bot.delete_message(message.chat.id, old_id)
        except Exception:
            pass
    sent = await message.answer(text, reply_markup=user_keyboard(is_form=True))
    await state.update_data(prompt_id=sent.message_id)


async def _show_draft(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    preview_text = (
        "<b>👀 TAVSIYANGIZNI TEKSHIRING</b>\n\n"
        f"📖 <b>{html(data.get('title', ''))}</b>\n"
        f"✍️ <i>{html(data.get('author', ''))}</i>\n\n"
        f"💭 <blockquote>{html(data.get('review', ''))}</blockquote>\n"
        f"🖼 Rasm: {'✅' if data.get('photo_file_id') else '—'}\n\n"
        "Hammasi to‘g‘ri bo‘lsa, <b>✅ Yuborish</b>ni bosing."
    )
    old_id = data.get("preview_id") or data.get("prompt_id")
    if old_id:
        try:
            await call.bot.delete_message(call.message.chat.id, old_id)
        except Exception:
            pass
    msg = await call.message.answer(preview_text, reply_markup=draft_edit_keyboard())
    await state.update_data(preview_id=msg.message_id)


@router.message(F.text == UserButtons.RECOMMEND)
async def recommend_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(RecommendationFlow.title)
    await _next_prompt(message, state, "📖 <b>Kitob nomini yuboring.</b>\n\n<i>Masalan: O‘tkan kunlar</i>")


@router.message(RecommendationFlow.title)
async def rec_title(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("edit_field") == "title":
        await state.update_data(title=(message.text or "").strip(), edit_field=None)
        await _show_draft_from_message(message, state)
        return
    title = (message.text or "").strip()
    if len(title) < 2 or len(title) > 300:
        await _next_prompt(message, state, "⚠️ Kitob nomi 2–300 belgi oralig‘ida bo‘lsin.\n\n📖 Qaytadan kiriting:")
        return
    await state.update_data(title=title)
    await state.set_state(RecommendationFlow.author)
    await _next_prompt(message, state, "✍️ <b>Muallif nomini yuboring.</b>")


@router.message(RecommendationFlow.author)
async def rec_author(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("edit_field") == "author":
        await state.update_data(author=(message.text or "").strip(), edit_field=None)
        await _show_draft_from_message(message, state)
        return
    author = (message.text or "").strip()
    if len(author) < 2 or len(author) > 300:
        await _next_prompt(message, state, "⚠️ Muallif nomi 2–300 belgi oralig‘ida bo‘lsin.\n\n✍️ Qaytadan kiriting:")
        return
    await state.update_data(author=author)
    await state.set_state(RecommendationFlow.review)
    await _next_prompt(message, state, "💭 <b>Nega bu kitobni tavsiya qilasiz?</b>\n\n<i>Qisqa, mazmunli fikr yozing.</i>")


@router.message(RecommendationFlow.review)
async def rec_review(message: Message, state: FSMContext, settings):
    data = await state.get_data()
    if data.get("edit_field") == "review":
        await state.update_data(review=(message.text or "").strip(), edit_field=None)
        await _show_draft_from_message(message, state)
        return
    review = (message.text or "").strip()
    if len(review) < 10 or len(review) > settings.max_review_length:
        await _next_prompt(message, state, f"⚠️ Fikr 10–{settings.max_review_length} belgi oralig‘ida bo‘lsin.\n\n💭 Qaytadan yuboring:")
        return
    await state.update_data(review=review)
    await state.set_state(RecommendationFlow.photo)
    await _next_prompt(message, state, "🖼 <b>Kitob rasmini yuboring.</b>\n\nAgar rasm bo‘lmasa, <code>rasmsiz</code> deb yozing.")


@router.message(RecommendationFlow.photo)
async def rec_photo(message: Message, state: FSMContext):
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif (message.text or "").strip().lower() in {"rasmsiz", "yo‘q", "yoq", "no"}:
        photo_id = None
    else:
        await _next_prompt(message, state, "🖼 Rasm yuboring yoki <code>rasmsiz</code> deb yozing.")
        return
    await state.update_data(photo_file_id=photo_id)
    data = await state.get_data()
    old_id = data.get("prompt_id")
    if old_id:
        try:
            await message.bot.delete_message(message.chat.id, old_id)
        except Exception:
            pass
    preview = await message.answer(
        "<b>👀 TAVSIYANGIZNI TEKSHIRING</b>\n\n"
        f"📖 <b>{html(data['title'])}</b>\n"
        f"✍️ <i>{html(data['author'])}</i>\n\n"
        f"💭 <blockquote>{html(data['review'])}</blockquote>\n"
        f"🖼 Rasm: {'✅' if photo_id else '—'}\n\n"
        "Hammasi to‘g‘ri bo‘lsa, <b>✅ Yuborish</b>ni bosing.",
        reply_markup=draft_edit_keyboard(),
    )
    await state.update_data(preview_id=preview.message_id)


@router.callback_query(F.data == "draftedit:done")
async def draft_done(call: CallbackQuery, state: FSMContext, repo: Repository, settings):
    data = await state.get_data()
    if not all(data.get(k) for k in ("title", "author", "review")):
        await call.answer("⚠️ Tavsiya ma’lumotlari to‘liq emas.", show_alert=True)
        return
    rec = await repo.create_recommendation(
        call.from_user.id,
        data["title"],
        data["author"],
        data["review"],
        data.get("photo_file_id"),
    )
    await state.clear()
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer(
        f"✅ <b>Tavsiyangiz qabul qilindi.</b>\n\n🆔 #{rec.id}\n🟡 Holat: <b>Ko‘rib chiqilmoqda</b>",
        reply_markup=user_keyboard(),
    )
    await notify_recommendation(call.bot, repo, settings.admin_ids, rec.id)
    await call.answer("✅ Yuborildi!")


@router.callback_query(F.data.startswith("draftedit:"))
async def draft_edit_start(call: CallbackQuery, state: FSMContext):
    field = call.data.split(":", 1)[1]
    if field not in {"title", "author", "review"}:
        await call.answer()
        return
    await state.update_data(edit_field=field)
    prompts = {
        "title": "📖 Yangi kitob nomini yuboring:",
        "author": "✍️ Yangi muallif nomini yuboring:",
        "review": "💭 Yangi fikrni yuboring:",
    }
    await call.message.answer(prompts[field], reply_markup=user_keyboard(is_form=True))
    await state.set_state(RecommendationFlow.review if field == "review" else RecommendationFlow.author if field == "author" else RecommendationFlow.title)
    await call.answer()


async def _show_draft_from_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    try:
        await message.delete()
    except Exception:
        pass
    old_id = data.get("preview_id")
    if old_id:
        try:
            await message.bot.delete_message(message.chat.id, old_id)
        except Exception:
            pass
    preview = await message.answer(
        "<b>👀 TAVSIYANGIZ</b>\n\n"
        f"📖 <b>{html(data.get('title',''))}</b>\n"
        f"✍️ <i>{html(data.get('author',''))}</i>\n\n"
        f"💭 <blockquote>{html(data.get('review',''))}</blockquote>\n"
        f"🖼 Rasm: {'✅' if data.get('photo_file_id') else '—'}",
        reply_markup=draft_edit_keyboard(),
    )
    await state.update_data(preview_id=preview.message_id)


@router.callback_query(F.data == "rec:cancel")
async def cancel_preview(call: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer("↩️ Tavsiya bekor qilindi.", reply_markup=user_keyboard())
    await call.answer()


@router.message(F.text == UserButtons.MY_RECS)
async def my_recs(message: Message, repo: Repository):
    recs = await repo.list_user_recommendations(message.from_user.id)
    if not recs:
        await message.answer("📚 Hozircha yuborgan tavsiyangiz yo‘q.", reply_markup=user_keyboard())
        return
    lines = ["<b>📚 MENING TAVSIYALARIM</b>", ""]
    for rec in recs:
        lines.append(f"<b>#{rec.id}</b> — {html(rec.title)}\n{status_label(rec.status)}")
    await message.answer("\n\n".join(lines), reply_markup=user_keyboard())


@router.message(F.text == UserButtons.RULES)
async def rules(message: Message):
    await message.answer(rules_text(), reply_markup=user_keyboard())


@router.message(F.text == UserButtons.CHANNEL)
async def channel(message: Message, repo: Repository):
    url = await repo.get_setting("target_channel_url", "")
    if url:
        await message.answer(f"📢 <b>Kanalimiz</b>\n\n{html(url)}", reply_markup=user_keyboard())
    else:
        await message.answer("📢 Kanal manzili hozircha sozlanmagan.", reply_markup=user_keyboard())
