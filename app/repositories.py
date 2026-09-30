from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import aliased

from .db import Database
from .models import BotSetting, Recommendation, SupportTicket, User
from .utils import normalize_book


class Repository:
    def __init__(self, db: Database):
        self.db = db

    async def upsert_user(self, tg_user) -> User:
        now = datetime.now(timezone.utc)
        async with self.db.session() as session:
            user = await session.get(User, tg_user.id)
            if user is None:
                user = User(id=tg_user.id)
                session.add(user)
            user.username = tg_user.username
            user.first_name = tg_user.first_name
            user.last_name = tg_user.last_name
            user.last_seen_at = now
            await session.commit()
            return user

    async def get_user(self, user_id: int) -> User | None:
        async with self.db.session() as session:
            return await session.get(User, user_id)

    async def set_blocked(self, user_id: int, blocked: bool) -> None:
        async with self.db.session() as session:
            user = await session.get(User, user_id)
            if user:
                user.is_blocked = blocked
                await session.commit()

    async def search_users(self, query: str, limit: int = 10) -> list[User]:
        async with self.db.session() as session:
            stmt = select(User)
            q = query.strip().lstrip("@")
            if q.isdigit():
                stmt = stmt.where(User.id == int(q))
            else:
                like = f"%{q}%"
                stmt = stmt.where(or_(User.username.ilike(like), User.first_name.ilike(like), User.last_name.ilike(like)))
            stmt = stmt.order_by(User.last_seen_at.desc()).limit(limit)
            return list((await session.execute(stmt)).scalars())

    async def create_recommendation(self, user_id: int, title: str, author: str, review: str, photo_file_id: str | None) -> Recommendation:
        key = normalize_book(title, author)
        async with self.db.session() as session:
            duplicate = (await session.execute(
                select(Recommendation).where(
                    Recommendation.normalized_key == key,
                    Recommendation.status.in_(["pending", "publishing", "published"]),
                ).order_by(Recommendation.created_at.desc()).limit(1)
            )).scalar_one_or_none()
            rec = Recommendation(
                user_id=user_id,
                title=title.strip(),
                author=author.strip(),
                review=review.strip(),
                photo_file_id=photo_file_id,
                normalized_key=key,
                duplicate_of_id=duplicate.id if duplicate else None,
            )
            session.add(rec)
            await session.commit()
            await session.refresh(rec)
            return rec

    async def get_recommendation(self, rec_id: int) -> Recommendation | None:
        async with self.db.session() as session:
            return await session.get(Recommendation, rec_id)

    async def list_user_recommendations(self, user_id: int, limit: int = 15) -> list[Recommendation]:
        async with self.db.session() as session:
            stmt = select(Recommendation).where(Recommendation.user_id == user_id).order_by(Recommendation.created_at.desc()).limit(limit)
            return list((await session.execute(stmt)).scalars())

    async def list_pending_recommendations(self, limit: int = 10) -> list[Recommendation]:
        async with self.db.session() as session:
            stmt = select(Recommendation).where(Recommendation.status == "pending").order_by(Recommendation.created_at.asc()).limit(limit)
            return list((await session.execute(stmt)).scalars())

    async def claim_recommendation(self, rec_id: int) -> bool:
        async with self.db.session() as session:
            result = await session.execute(
                update(Recommendation)
                .where(Recommendation.id == rec_id, Recommendation.status == "pending")
                .values(status="publishing", updated_at=datetime.now(timezone.utc))
            )
            await session.commit()
            return result.rowcount == 1

    async def mark_published(self, rec_id: int, message_id: int) -> None:
        async with self.db.session() as session:
            rec = await session.get(Recommendation, rec_id)
            if rec:
                rec.status = "published"
                rec.published_message_id = message_id
                rec.updated_at = datetime.now(timezone.utc)
                await session.commit()

    async def return_to_pending(self, rec_id: int) -> None:
        async with self.db.session() as session:
            rec = await session.get(Recommendation, rec_id)
            if rec and rec.status == "publishing":
                rec.status = "pending"
                rec.updated_at = datetime.now(timezone.utc)
                await session.commit()

    async def reject_recommendation(self, rec_id: int, reason: str) -> int | None:
        async with self.db.session() as session:
            rec = await session.get(Recommendation, rec_id)
            if not rec or rec.status not in {"pending", "publishing"}:
                return None
            rec.status = "rejected"
            rec.reject_reason = reason.strip()
            rec.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return rec.user_id

    async def edit_recommendation(self, rec_id: int, field: str, value: str) -> bool:
        if field not in {"title", "author", "review"}:
            return False
        async with self.db.session() as session:
            rec = await session.get(Recommendation, rec_id)
            if not rec or rec.status not in {"pending", "publishing"}:
                return False
            setattr(rec, field, value.strip())
            rec.normalized_key = normalize_book(rec.title, rec.author)
            rec.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return True

    async def ensure_defaults(self, defaults: dict[str, str]) -> None:
        async with self.db.session() as session:
            for key, value in defaults.items():
                obj = await session.get(BotSetting, key)
                if obj is None:
                    session.add(BotSetting(key=key, value=value))
            await session.commit()

    async def get_setting(self, key: str, default: str = "") -> str:
        async with self.db.session() as session:
            obj = await session.get(BotSetting, key)
            return obj.value if obj else default

    async def set_setting(self, key: str, value: str) -> None:
        async with self.db.session() as session:
            obj = await session.get(BotSetting, key)
            if obj is None:
                obj = BotSetting(key=key, value=value)
                session.add(obj)
            else:
                obj.value = value
            obj.updated_at = datetime.now(timezone.utc)
            await session.commit()

    async def get_settings(self) -> dict[str, str]:
        async with self.db.session() as session:
            rows = (await session.execute(select(BotSetting))).scalars()
            return {row.key: row.value for row in rows}

    async def create_ticket(self, user_id: int, text: str) -> SupportTicket:
        async with self.db.session() as session:
            ticket = SupportTicket(user_id=user_id, message_text=text.strip())
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            return ticket

    async def open_tickets(self, limit: int = 20) -> list[SupportTicket]:
        async with self.db.session() as session:
            stmt = select(SupportTicket).where(SupportTicket.status == "open").order_by(SupportTicket.created_at.asc()).limit(limit)
            return list((await session.execute(stmt)).scalars())

    async def get_ticket(self, ticket_id: int) -> SupportTicket | None:
        async with self.db.session() as session:
            return await session.get(SupportTicket, ticket_id)

    async def reply_ticket(self, ticket_id: int, admin_id: int, reply: str) -> int | None:
        async with self.db.session() as session:
            ticket = await session.get(SupportTicket, ticket_id)
            if not ticket:
                return None
            ticket.admin_id = admin_id
            ticket.admin_reply = reply.strip()
            ticket.status = "closed"
            ticket.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return ticket.user_id

    async def reopen_ticket(self, ticket_id: int) -> None:
        async with self.db.session() as session:
            ticket = await session.get(SupportTicket, ticket_id)
            if ticket:
                ticket.status = "open"
                ticket.updated_at = datetime.now(timezone.utc)
                await session.commit()

    async def close_ticket(self, ticket_id: int) -> None:
        async with self.db.session() as session:
            ticket = await session.get(SupportTicket, ticket_id)
            if ticket:
                ticket.status = "closed"
                ticket.updated_at = datetime.now(timezone.utc)
                await session.commit()

    async def broadcast_users(self) -> list[int]:
        async with self.db.session() as session:
            stmt = select(User.id).where(User.is_blocked.is_(False))
            return [x for x in (await session.execute(stmt)).scalars().all()]

    async def stats(self) -> dict[str, int]:
        async with self.db.session() as session:
            vals = {}
            vals["users"] = await session.scalar(select(func.count()).select_from(User)) or 0
            vals["pending"] = await session.scalar(select(func.count()).select_from(Recommendation).where(Recommendation.status == "pending")) or 0
            vals["published"] = await session.scalar(select(func.count()).select_from(Recommendation).where(Recommendation.status == "published")) or 0
            vals["rejected"] = await session.scalar(select(func.count()).select_from(Recommendation).where(Recommendation.status == "rejected")) or 0
            vals["tickets"] = await session.scalar(select(func.count()).select_from(SupportTicket).where(SupportTicket.status == "open")) or 0
            return {k: int(v) for k,v in vals.items()}

    async def recover_stuck_publishing(self, minutes: int = 15) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        async with self.db.session() as session:
            result = await session.execute(
                update(Recommendation)
                .where(Recommendation.status == "publishing", Recommendation.updated_at < cutoff)
                .values(status="pending", updated_at=datetime.now(timezone.utc))
            )
            await session.commit()
            return result.rowcount
