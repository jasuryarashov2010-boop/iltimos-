from __future__ import annotations

from .settings import DEFAULTS
from ..utils import html


def render_recommendation(title: str, author: str, review: str, header: str, footer: str) -> str:
    header = header or DEFAULTS["post_header"]
    footer = footer or DEFAULTS["post_footer"]
    return (
        f"<b>╭━━━━━━━━━━━━━━━━━━━━╮</b>\n"
        f"<b>  {html(header)}</b>\n"
        f"<b>╰━━━━━━━━━━━━━━━━━━━━╯</b>\n\n"
        f"📖 <b>{html(title)}</b>\n"
        f"✍️ <i>{html(author)}</i>\n\n"
        f"💭 <b>Kitobxon fikri</b>\n"
        f"<blockquote>{html(review)}</blockquote>\n\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"{html(footer)}"
    )
