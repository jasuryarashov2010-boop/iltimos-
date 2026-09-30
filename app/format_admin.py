from __future__ import annotations

from ..utils import html


def recommendation_admin_text(rec, duplicate_note: str = "") -> str:
    user = f"<code>{rec.user_id}</code>"
    note = f"\n⚠️ <b>Duplicate:</b> #{rec.duplicate_of_id}" if rec.duplicate_of_id else ""
    if duplicate_note:
        note += f"\n{html(duplicate_note)}"
    return (
        f"<b>📥 YANGI KITOB TAVSIYASI #{rec.id}</b>{note}\n\n"
        f"📖 <b>{html(rec.title)}</b>\n"
        f"✍️ <i>{html(rec.author)}</i>\n\n"
        f"💭 <b>Fikr:</b>\n<blockquote>{html(rec.review)}</blockquote>\n\n"
        f"👤 User ID: {user}\n"
        f"📅 {rec.created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"🟡 Holat: <b>{html(rec.status)}</b>"
    )
