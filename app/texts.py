from dataclasses import dataclass


class UserButtons:
    RECOMMEND = "📖 Kitob tavsiya qilish"
    MY_RECS = "📚 Mening tavsiyalarim"
    SUPPORT = "💬 Adminga yozish"
    RULES = "ℹ️ Tavsiya qoidalari"
    CHANNEL = "📢 Kanalimiz"
    CANCEL = "❌ Bekor qilish"
    HOME = "🏠 Bosh menyu"


class AdminButtons:
    RECOMMENDATIONS = "📥 Tavsiyalar"
    TICKETS = "📨 Murojaatlar"
    BROADCAST = "📣 Barchaga xabar"
    DESIGN = "🎨 Post dizayni"
    REACTION = "🔥 Reaksiya"
    CHANNEL = "📢 Kanal sozlamalari"
    USERS = "👥 Foydalanuvchilar"
    STATS = "📊 Statistika"
    SYSTEM = "⚙️ Tizim"
    HOME = "🏠 Bosh menyu"


@dataclass(frozen=True)
class Copy:
    title: str = "📚 <b>Kitobxon</b>"


COPY = Copy()


def main_menu(is_admin: bool = False) -> str:
    admin_line = "\n👑 <b>Admin panel</b> siz uchun pastdagi menyuda mavjud." if is_admin else ""
    return (
        "<b>╭━━━━━━━━━━━━━━━━━━━━╮</b>\n"
        "<b>      📚 KITOBXON</b>\n"
        "<b>╰━━━━━━━━━━━━━━━━━━━━╯</b>\n\n"
        "📖 O‘qigan kitobingizni boshqalarga tavsiya qiling.\n"
        "💬 Fikringizni yuboring — qolganini biz qilamiz.\n\n"
        "<i>Har bir tavsiya admin tomonidan tekshiriladi.</i>"
        f"{admin_line}"
    )


def subscription_text() -> str:
    return (
        "<b>🔐 Botdan foydalanishdan oldin kanalga obuna bo‘ling.</b>\n\n"
        "1️⃣ Kanalga qo‘shiling\n"
        "2️⃣ <b>✅ Obunani tekshirish</b> tugmasini bosing"
    )


def rules_text() -> str:
    return (
        "<b>ℹ️ TAVSIYA QOIDALARI</b>\n\n"
        "• 📖 O‘qigan kitobingizni yuboring.\n"
        "• ✍️ Kitob nomi va muallifini to‘g‘ri yozing.\n"
        "• 💭 Fikringizni mazmunli va odobli yozing.\n"
        "• 🚫 Reklama, spam va nomaqbul matn yubormang.\n\n"
        "✅ Har bir tavsiya admin tomonidan ko‘rib chiqiladi."
    )


def status_label(status: str) -> str:
    return {
        "pending": "🟡 Ko‘rib chiqilmoqda",
        "publishing": "🔵 Kanalga tayyorlanmoqda",
        "published": "🟢 Kanalga joylangan",
        "rejected": "🔴 Rad etilgan",
    }.get(status, status)
