from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from .texts import AdminButtons, UserButtons


def user_keyboard(is_form: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=UserButtons.RECOMMEND)],
        [KeyboardButton(text=UserButtons.MY_RECS), KeyboardButton(text=UserButtons.SUPPORT)],
        [KeyboardButton(text=UserButtons.RULES), KeyboardButton(text=UserButtons.CHANNEL)],
    ]
    if is_form:
        rows.append([KeyboardButton(text=UserButtons.CANCEL)])
    else:
        rows.append([KeyboardButton(text=UserButtons.HOME)])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Menyu orqali tanlang…",
    )


def admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=AdminButtons.RECOMMENDATIONS), KeyboardButton(text=AdminButtons.TICKETS)],
            [KeyboardButton(text=AdminButtons.BROADCAST), KeyboardButton(text=AdminButtons.DESIGN)],
            [KeyboardButton(text=AdminButtons.REACTION), KeyboardButton(text=AdminButtons.CHANNEL)],
            [KeyboardButton(text=AdminButtons.USERS), KeyboardButton(text=AdminButtons.STATS)],
            [KeyboardButton(text=AdminButtons.SYSTEM), KeyboardButton(text=AdminButtons.HOME)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Admin bo‘limini tanlang…",
    )


def subscription_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga qo‘shilish", url=url)],
        [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="sub:check")],
    ])


def recommendation_preview_keyboard(rec_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yuborish", callback_data=f"rec:confirm:{rec_id}"),
         InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"rec:edit:{rec_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="rec:cancel")],
    ])


def admin_recommendation_keyboard(rec_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👀 Preview", callback_data=f"admrec:preview:{rec_id}"),
         InlineKeyboardButton(text="✅ Joylash", callback_data=f"admrec:publish:{rec_id}")],
        [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"admrec:reject:{rec_id}"),
         InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"admrec:edit:{rec_id}")],
    ])


def rec_edit_keyboard(rec_id: int, owner: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📖 Kitob nomi", callback_data=f"recedit:title:{rec_id}"),
         InlineKeyboardButton(text="✍️ Muallif", callback_data=f"recedit:author:{rec_id}")],
        [InlineKeyboardButton(text="💭 Fikr", callback_data=f"recedit:review:{rec_id}")],
    ]
    if owner:
        buttons.append([InlineKeyboardButton(text="✅ Saqlash", callback_data="rec:edit_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def reject_confirm_keyboard(rec_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Rad etishni tasdiqlash", callback_data=f"reject:confirm:{rec_id}"),
         InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admrec:preview:{rec_id}")]
    ])


def user_result_keyboard(user_id: int, blocked: bool) -> InlineKeyboardMarkup:
    action = "✅ Blokdan chiqarish" if blocked else "🚫 Bloklash"
    action_code = "unblock" if blocked else "block"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=action, callback_data=f"user:{action_code}:{user_id}")]
    ])


def ticket_keyboard(ticket_id: int, status: str) -> InlineKeyboardMarkup:
    if status != "open":
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="↩️ Qayta ochish", callback_data=f"ticket:reopen:{ticket_id}")
        ]])
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="↩️ Javob berish", callback_data=f"ticket:reply:{ticket_id}"),
        InlineKeyboardButton(text="✅ Yopish", callback_data=f"ticket:close:{ticket_id}")
    ]])


def broadcast_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast:send"),
         InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast:cancel")]
    ])


def reaction_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Emoji o‘zgartirish", callback_data="reaction:set")],
        [InlineKeyboardButton(text=("✅ Faol" if enabled else "❌ O‘chirilgan"), callback_data="reaction:toggle")]
    ])


def design_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪧 Header", callback_data="design:header"),
         InlineKeyboardButton(text="🔚 Footer", callback_data="design:footer")],
        [InlineKeyboardButton(text="↩️ Standartga qaytarish", callback_data="design:reset")]
    ])


def channel_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Post kanal ID", callback_data="channel:target_id"),
         InlineKeyboardButton(text="🔗 Post kanal URL", callback_data="channel:target_url")],
        [InlineKeyboardButton(text="🔐 Obuna kanal ID", callback_data="channel:sub_id"),
         InlineKeyboardButton(text="🔗 Obuna kanal URL", callback_data="channel:sub_url")],
        [InlineKeyboardButton(text="🔐 Obunani yoqish/o‘chirish", callback_data="channel:sub_toggle")],
    ])
