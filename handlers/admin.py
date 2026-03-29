from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from config import ADMIN_IDS
from database import Lead, Tour, User, async_session, get_user, set_role, upsert_manager
from keyboards import admin_menu

router = Router()


def _guard(uid: int) -> bool:
    return uid in ADMIN_IDS


# ── Commands ───────────────────────────────────────────────────────────────────

@router.message(Command("add_manager"))
async def add_manager(message: Message, bot: Bot) -> None:
    if not _guard(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("Использование: <code>/add_manager USER_ID</code>")
        return
    target_id = int(args[1])
    user = await upsert_manager(target_id)
    await message.answer(f"✅ <b>{user.name}</b> (<code>{target_id}</code>) — теперь менеджер.")
    try:
        await bot.send_message(target_id, "🎉 Вы назначены менеджером Sofia Travel!\nНажмите /start.")
    except Exception:
        await message.answer("⚠️ Не удалось уведомить пользователя (он ещё не запускал бота).")


@router.message(Command("remove_manager"))
async def remove_manager(message: Message) -> None:
    if not _guard(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("Использование: <code>/remove_manager USER_ID</code>")
        return
    target_id = int(args[1])
    user = await set_role(target_id, "client")
    if not user:
        await message.answer("❌ Пользователь не найден в БД.")
        return
    await message.answer(f"✅ <b>{user.name}</b> больше не менеджер.")


# ── Menu buttons ───────────────────────────────────────────────────────────────

@router.message(F.text == "➕ Добавить менеджера")
async def hint_add(message: Message) -> None:
    if not _guard(message.from_user.id):
        return
    await message.answer(
        "Отправьте команду:\n<code>/add_manager USER_ID</code>\n\n"
        "USER_ID — Telegram ID пользователя (узнать: @userinfobot)"
    )


@router.message(F.text == "➖ Удалить менеджера")
async def hint_remove(message: Message) -> None:
    if not _guard(message.from_user.id):
        return
    await message.answer("Отправьте команду:\n<code>/remove_manager USER_ID</code>")


@router.message(F.text == "📊 Все заявки")
async def all_leads(message: Message) -> None:
    if not _guard(message.from_user.id):
        return
    async with async_session() as s:
        leads = (
            await s.execute(select(Lead).order_by(Lead.created_at.desc()).limit(25))
        ).scalars().all()

    if not leads:
        await message.answer("Заявок пока нет.")
        return

    icons = {"new": "🆕", "in_progress": "🔄", "closed": "✅"}
    text = "📊 <b>Все заявки (последние 25):</b>\n\n"
    for lead in leads:
        icon = icons.get(lead.status, "❓")
        country = f" · {lead.country}" if lead.country else ""
        mgr = f"mgr <code>{lead.manager_id}</code>" if lead.manager_id else "без менеджера"
        text += f"{icon} №{lead.id}{country} | клиент <code>{lead.user_id}</code> | {mgr}\n"
    await message.answer(text)


@router.message(F.text == "👥 Пользователи")
async def all_users(message: Message) -> None:
    if not _guard(message.from_user.id):
        return
    async with async_session() as s:
        users = (await s.execute(select(User).order_by(User.created_at.desc()))).scalars().all()

    icons = {"admin": "👑", "manager": "💼", "client": "👤"}
    text = f"👥 <b>Пользователи ({len(users)}):</b>\n\n"
    for u in users:
        icon = icons.get(u.role, "👤")
        text += f"{icon} <b>{u.name}</b> | <code>{u.user_id}</code> | {u.role}\n"
    await message.answer(text)


@router.message(F.text == "🏝 Туры")
async def admin_tours(message: Message) -> None:
    if not _guard(message.from_user.id):
        return
    async with async_session() as s:
        tours = (await s.execute(select(Tour).order_by(Tour.created_at.desc()))).scalars().all()

    if not tours:
        await message.answer("Туров пока нет.\n\nДобавить: /add_tour")
        return

    text = f"🏝 <b>Все туры ({len(tours)}):</b>\n\n"
    for t in tours:
        text += f"• <b>{t.title}</b> | {t.country} | {t.price} | {t.dates}\n"
    text += "\n/add_tour — добавить новый тур"
    await message.answer(text)
