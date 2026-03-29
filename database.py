from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DATABASE_URL = "sqlite+aiosqlite:///aya_bot.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), default="")
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    tg_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="ru")
    role: Mapped[str] = mapped_column(String(20), default="client")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    budget: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dates: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tour_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="new")
    manager_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    ai_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tour_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tours.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Tour(Base):
    __tablename__ = "tours"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    country: Mapped[str] = mapped_column(String(100))
    price: Mapped[str] = mapped_column(String(100))
    dates: Mapped[str] = mapped_column(String(100))
    added_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── Helpers ────────────────────────────────────────────────────────────────────

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_user(user_id: int) -> Optional[User]:
    async with async_session() as s:
        return await s.get(User, user_id)


async def create_user(user_id: int, name: str, language: str, role: str = "client",
                      age: int = None, phone: str = None, tg_username: str = None) -> User:
    async with async_session() as s:
        user = User(user_id=user_id, name=name, language=language, role=role,
                    age=age, phone=phone, tg_username=tg_username)
        s.add(user)
        await s.commit()
        return user


async def upsert_manager(user_id: int) -> User:
    async with async_session() as s:
        user = await s.get(User, user_id)
        if user:
            user.role = "manager"
        else:
            user = User(user_id=user_id, name=f"Manager_{user_id}", language="ru", role="manager")
            s.add(user)
        await s.commit()
        return user


async def set_role(user_id: int, role: str) -> Optional[User]:
    async with async_session() as s:
        user = await s.get(User, user_id)
        if not user:
            return None
        user.role = role
        await s.commit()
        return user


async def get_active_relay_lead(user_id: int) -> Optional[Lead]:
    async with async_session() as s:
        result = await s.execute(
            select(Lead).where(
                Lead.user_id == user_id,
                Lead.status == "in_progress",
                Lead.ai_active == False,
                Lead.manager_id.isnot(None),
            ).limit(1)
        )
        return result.scalar_one_or_none()
