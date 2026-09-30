from app.utils import normalize_book, trim


def test_normalize_book_stable():
    assert normalize_book("  O'tkan   kunlar ", "Abdulla Qodiriy") == normalize_book("O'tkan kunlar", "Abdulla Qodiriy")


def test_trim():
    assert trim("abcdef", 5) == "abcd…"
