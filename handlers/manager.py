import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from config import ADMIN_IDS
from database import Lead, Tour, User, async_session, get_user
from keyboards import cancel_kb, lead_actions_kb, manager_menu
from states import AddTour, ManagerStates

router = Router()
log = logging.getLogger(__name__)


def _is_staff(uid: int) -> bool:
    return uid in ADMIN_IDS


async def _is_manager_or_admin(uid: int) -> bool:
    if uid in ADMIN_IDS:
        return True
    user = await get_user(uid)
    return user is not None and user.role == "manager"


# ── View leads ─────────────────────────────────────────────────────────────────

@router.message(F.text == "📥 Новые заявки")
async def new_leads(message: Message) -> None:
    user = await get_user(message.from_user.id)
    if not user or user.role != "manager":
        return
    async with async_session() as s:
        leads = (
            await s.execute(select(Lead).where(Lead.status == "new").order_by(Lead.created_at.desc()))
        ).scalars().all()

    if not leads:
        await message.answer("📭 Новых заявок нет.")
        return

    for lead in leads:
        client = await get_user(lead.user_id)
        uname = f"@{client.tg_username}" if client and client.tg_username else "—"
        text = (
            f"📋 <b>Заявка №{lead.id}</b>\n\n"
            f"👤 <b>Клиент:</b>\n"
            f"Имя: {client.name if client else '—'}\n"
            f"Возраст: {client.age if client else '—'}\n"
            f"Телефон: {client.phone if client else '—'}\n"
            f"Telegram: {uname}\n\n"
            f"🌍 <b>Тур:</b>\n"
            f"Страна: {lead.country or '—'}\n"
            f"Бюджет: {lead.budget or '—'}\n"
            f"Даты: {lead.dates or '—'}\n"
            f"Тип отдыха: {lead.tour_type or '—'}"
        )
        await message.answer(text, reply_markup=lead_actions_kb(lead.id, lead.user_id))


@router.message(F.text == "📊 Все мои заявки")
async def all_my_leads(message: Message) -> None:
    user = await get_user(message.from_user.id)
    if not user or user.role != "manager":
        return
    async with async_session() as s:
        leads = (
            await s.execute(
                select(Lead).where(Lead.manager_id == message.from_user.id).order_by(Lead.created_at.desc())
            )
        ).scalars().all()

    if not leads:
        await message.answer("У вас нет заявок в работе.")
        return

    icons = {"new": "🆕", "in_progress": "🔄", "closed": "✅"}
    text = "📊 <b>Ваши заявки:</b>\n\n"
    for lead in leads:
        text += f"{icons.get(lead.status,'❓')} №{lead.id} | клиент <code>{lead.user_id}</code>\n"
    await message.answer(text)


# ── Tours (for manager) ────────────────────────────────────────────────────────

@router.message(F.text == "🏝 Туры")
async def list_tours_staff(message: Message) -> None:
    if not await _is_manager_or_admin(message.from_user.id):
        return
    async with async_session() as s:
        tours = (await s.execute(select(Tour).order_by(Tour.created_at.desc()))).scalars().all()

    if not tours:
        await message.answer("Туров пока нет. Добавьте: /add_tour")
        return

    text = "🏝 <b>Список туров:</b>\n\n"
    for t in tours:
        text += f"• <b>{t.title}</b> | {t.country} | {t.price} | {t.dates}\n"
    text += "\nДобавить: /add_tour"
    await message.answer(text)


# ── /add_tour FSM ──────────────────────────────────────────────────────────────

@router.message(Command("add_tour"))
async def add_tour_start(message: Message, state: FSMContext) -> None:
    if not await _is_manager_or_admin(message.from_user.id):
        return
    await message.answer("🏝 <b>Добавление нового тура</b>\n\nШаг 1/5 — Введите название тура:", reply_markup=cancel_kb())
    await state.set_state(AddTour.title)


@router.message(AddTour.title, F.text == "❌ Отмена")
@router.message(AddTour.description, F.text == "❌ Отмена")
@router.message(AddTour.country, F.text == "❌ Отмена")
@router.message(AddTour.price, F.text == "❌ Отмена")
@router.message(AddTour.dates, F.text == "❌ Отмена")
async def add_tour_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    uid = message.from_user.id
    kb = manager_menu() if uid not in ADMIN_IDS else None
    await message.answer("Отменено.", reply_markup=kb)


@router.message(AddTour.title, F.text)
async def add_tour_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await message.answer("Шаг 2/5 — Введите описание тура:")
    await state.set_state(AddTour.description)


@router.message(AddTour.description, F.text)
async def add_tour_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await message.answer("Шаг 3/5 — Страна:")
    await state.set_state(AddTour.country)


@router.message(AddTour.country, F.text)
async def add_tour_country(message: Message, state: FSMContext) -> None:
    await state.update_data(country=message.text.strip())
    await message.answer("Шаг 4/5 — Цена (например: от $500):")
    await state.set_state(AddTour.price)


@router.message(AddTour.price, F.text)
async def add_tour_price(message: Message, state: FSMContext) -> None:
    await state.update_data(price=message.text.strip())
    await message.answer("Шаг 5/5 — Даты (например: Июнь 2025):")
    await state.set_state(AddTour.dates)


@router.message(AddTour.dates, F.text)
async def add_tour_dates(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    async with async_session() as s:
        tour = Tour(
            title=data["title"],
            description=data["description"],
            country=data["country"],
            price=data["price"],
            dates=message.text.strip(),
            added_by=message.from_user.id,
        )
        s.add(tour)
        await s.commit()
        await s.refresh(tour)

    await message.answer(
        f"✅ <b>Тур «{tour.title}» добавлен!</b>\n\n"
        f"📍 {tour.country} | 💰 {tour.price} | 📅 {tour.dates}\n\n"
        f"Клиенты уже могут его видеть в разделе 🔥 Доступные туры",
        reply_markup=manager_menu() if message.from_user.id not in ADMIN_IDS else None,
    )


# ── Inline: take / reply ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("take:"))
async def take_lead(callback: CallbackQuery) -> None:
    _, lead_id, client_id = callback.data.split(":")
    lead_id, client_id = int(lead_id), int(client_id)
    mgr_id = callback.from_user.id

    async with async_session() as s:
        lead = await s.get(Lead, lead_id)
        if not lead:
            await callback.answer("Заявка не найдена.")
            return
        if lead.status == "in_progress":
            await callback.answer("Уже в работе.")
            return
        lead.status = "in_progress"
        lead.manager_id = mgr_id
        lead.ai_active = False
        await s.commit()

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ <b>Взята в работу</b> | <code>{mgr_id}</code>"
    )
    await callback.answer("✅ Заявка взята!")


@router.callback_query(F.data.startswith("reply:"))
async def reply_lead_start(callback: CallbackQuery, state: FSMContext) -> None:
    _, lead_id, client_id = callback.data.split(":")
    lead_id, client_id = int(lead_id), int(client_id)
    mgr_id = callback.from_user.id

    async with async_session() as s:
        lead = await s.get(Lead, lead_id)
        if lead and lead.status == "new":
            lead.status = "in_progress"
            lead.manager_id = mgr_id
            lead.ai_active = False
            await s.commit()

    await state.update_data(lead_id=lead_id, client_id=client_id)
    await state.set_state(ManagerStates.replying)
    await callback.message.answer(
        f"✍️ Введите сообщение для клиента (заявка №{lead_id}):", reply_markup=cancel_kb()
    )
    await callback.answer()


@router.message(ManagerStates.replying, F.text == "❌ Отмена")
async def cancel_reply(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=manager_menu())


@router.message(ManagerStates.replying, F.text)
async def send_reply(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    lead_id = data.get("lead_id")
    client_id = data.get("client_id")
    try:
        await bot.send_message(
            client_id,
            f"💼 <b>Сообщение от менеджера (заявка №{lead_id}):</b>\n\n{message.text}",
        )
        await message.answer("✅ Отправлено клиенту!", reply_markup=manager_menu())
        await state.clear()
    except Exception as e:
        log.error(f"Reply send error: {e}")
        await message.answer(f"❌ Ошибка: {e}")
