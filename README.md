# 📚 Kitobxon V10

A production-oriented Telegram book recommendation/moderation bot for Render + PostgreSQL + Redis.

## 🎯 UX contract

**User**
- 🔐 Mandatory subscription
- 📖 Book recommendation flow
- 👀 Preview before submit
- 📚 My recommendations + statuses
- 💬 Contact admin
- 📢 Channel link
- Persistent Reply Keyboard

**Admin (exactly 2 IDs)**
- 📥 Moderation queue
- 👀 Channel preview
- ✅ Publish / ❌ Reject with reason / ✏️ Edit
- ⚠️ Duplicate detection
- 🎨 Post design
- 🔥 Reaction settings (admin types the emoji)
- 📢 Channel settings
- 👥 User search/block
- 📣 Broadcast
- 📨 Support inbox + replies
- 📊 Statistics
- ⚙️ System health

## 🧱 Architecture

`Telegram -> Router -> Middleware -> Handler -> Service -> Repository -> PostgreSQL`

Redis is used for FSM/session state. PostgreSQL stores durable application state. No `Base.metadata.create_all()` is used at runtime; database setup is migration-driven through Alembic. The initial migration uses idempotent PostgreSQL DDL and `CREATE INDEX IF NOT EXISTS` to avoid duplicate-index startup failures.

## 🔒 Design choices

- `/start` always clears FSM state and always works for admins.
- Admin navigation uses **ReplyKeyboard**, not an HTML dashboard message.
- Inline keyboards are reserved for contextual actions (approve/reject/edit/preview).
- User prompts are replaced to keep the chat visually clean.
- Publishing uses an atomic status claim so two admins cannot publish the same recommendation twice.
- Publishing failures return the recommendation to `pending`.
- A stuck `publishing` record older than 15 minutes is recovered at startup.
- Missing Redis falls back to MemoryStorage for local resilience; `/health` reports this as degraded.
- Missing channel configuration does not crash startup; the admin configures it from the bot.

## 🚀 Render

Build:

```bash
pip install -r requirements.txt
```

Start:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Health: `/health`

Python is pinned to `3.13.5` to avoid accidental dependency/source-build changes on Render.

## 🔐 Required Render variables

- `BOT_TOKEN`
- `ADMIN_IDS=ID1,ID2`
- `BOT_USERNAME` (optional)
- `DATABASE_URL` (Blueprint links PostgreSQL automatically)
- `REDIS_URL` (Blueprint links Key Value automatically)
- `WEBHOOK_SECRET` (Blueprint generates it)
- `WEBHOOK_BASE_URL` (Blueprint derives it from `RENDER_EXTERNAL_URL`)

## 📢 Telegram permissions

The bot should be an administrator in:
1. the mandatory-subscription channel, so `getChatMember` can reliably verify membership;
2. the target posting channel, so it can publish and set reactions.

## 🔥 Reaction constraint

Telegram Bot API currently allows a non-Premium bot to set up to one reaction per message. V10 therefore stores one admin-selected emoji and applies that emoji automatically. The reaction is editable from the admin panel.

## 🧪 Validation

```bash
python scripts/validate_project.py
pytest -q
```

Full live Telegram/PostgreSQL/Redis integration testing still requires real credentials and infrastructure. The project therefore includes deterministic static tests and idempotent migrations to reduce deploy risk.

## 🧭 GitHub reference survey

V10 was informed by patterns observed in 20 public repositories/templates, without copying their implementation code:

1. `andrew000/aiogram-template` — layered stack, Redis/Postgres, Caddy, CI
2. `donBarbos/telegram-bot-template` — Postgres, Redis, PgBouncer, monitoring
3. `ulugby/aiogram3-bot-template` — modern Router/FSM, reply+inline keyboards, tests
4. `Er1one/telegram-bot-template` — webhook, Postgres/Redis, tests, logging
5. `mxmrn/TgBotTemplate` — modular middleware/services, admin/broadcast
6. `NotBupyc/aiogram-bot-template` — Alembic, throttling, admin filter, logging
7. `bodaue/aiogram_v3_template` — SQLAlchemy async, asyncpg, Redis FSM, Alembic
8. `MrConsoleka/aiogram-bot-template` — DI, dialogs/FSM, optional FastAPI webhook
9. `arturboyun/AiogramBotTemplate` — SQLAlchemy, Alembic, FastAPI, Redis, Ruff
10. `czbag/aiogram-bot-template` — repository pattern, middleware, migration structure
11. `wakaree/aiogram_bot_template` — Handler→Flow→Interactor→Presenter separation
12. `Ralphcode-collab/aiogram3-bot-template` — webhook, rate limiting, ban guard, error handling
13. `NoBodyEver99/aiogram-bot-template` — admin, statistics, mailing, subscription management
14. `kama34/Aiogram-Bot-Template` — mandatory subscription, user management, admin dashboard ideas
15. `VernaculusF/aiogram3-bot-template` — access control, services/repositories, scheduler
16. `vkhnychenko/aiogram-template` — service-oriented architecture and strict typing
17. `VeryBigSad/telegram-bot-template` — FastAPI, webhook, Redis, logging/monitoring
18. `IronRom/aiogram-bot-template` — PostgreSQL, Redis, i18n-ready structure
19. `ALGOANHAF/telegram-bot-template` — auth middleware, ban/unban, broadcast patterns
20. `aiogram/aiogram` — authoritative framework patterns and official FSM/webhook behavior

Reference links are public and should be checked for their own licenses before reusing source code. V10 itself is a clean-room implementation.
