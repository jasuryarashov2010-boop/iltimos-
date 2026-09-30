from __future__ import annotations

import re
import unicodedata
from html import escape


def html(text: str | None) -> str:
    return escape(text or "", quote=False)


def normalize_book(title: str, author: str) -> str:
    title_clean = re.sub(r"\s+", " ", (title or "").strip())
    author_clean = re.sub(r"\s+", " ", (author or "").strip())
    raw = f"{title_clean}||{author_clean}".lower()
    raw = unicodedata.normalize("NFKC", raw)
    raw = re.sub(r"[​‌‍]", "", raw)
    raw = re.sub(r"[^\w|а-яёқғҳўáéíóúü\- ]+", "", raw, flags=re.IGNORECASE)
    return raw.strip()


def trim(text: str, max_len: int) -> str:
    text = text.strip()
    return text if len(text) <= max_len else text[: max_len - 1].rstrip() + "…"
