import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from ai_client import extract_lead_info, get_ai_response, get_chat_summary, reset_ai_history
from config import ADMIN_IDS
from database import Lead, Tour, User, async_session, get_user
from keyboards import ai_chat_kb, client_menu, lead_actions_kb, tour_apply_kb
from states import ClientStates
from stickers import get_sticker

router = Router()
log = logging.getLogger(__name__)


async def _sticker(message: Message, mood: str) -> None:
    try:
        await message.answer_sticker(get_sticker(mood))
    except Exception:
        pass


def _lead_manager_text(lead: Lead, user: User) -> str:
    uname = f"@{user.tg_username}" if user.tg_username else "—"
    country = lead.country or "не указано"
    budget = lead.budget or "не указано"
    dates = lead.dates or "не указано"
    tour_type = lead.tour_type or "не указано"
    return (
        f"📋 <b>Заявка №{lead.id}</b>\n\n"
        f"👤 <b>Клиент:</b>\n"
        f"Имя: {user.name}\n"
        f"Возраст: {user.age or '—'}\n"
        f"Телефон: {user.phone or '—'}\n"
        f"Telegram: {uname}\n\n"
        f"🌍 <b>Тур:</b>\n"
        f"Страна: {country}\n"
        f"Бюджет: {budget}\n"
        f"Даты: {dates}\n"
        f"Тип отдыха: {tour_type}"
    )


async def _notify_managers(bot: Bot, lead: Lead, user: User) -> None:
    async with async_session() as s:
        managers = (await s.execute(select(User).where(User.role == "manager"))).scalars().all()

    text = _lead_manager_text(lead, user)
    kb = lead_actions_kb(lead.id, lead.user_id)

    for mgr in managers:
        try:
            await bot.send_message(mgr.user_id, text, reply_markup=kb)
        except Exception as e:
            log.warning(f"Cannot notify manager {mgr.user_id}: {e}")
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, reply_markup=kb)
        except Exception:
            pass


# ── 🌍 Подобрать тур ───────────────────────────────────────────────────────────

@router.message(F.text == "🌍 Подобрать тур")
async def start_chat(message: Message, state: FSMContext) -> None:
    user = await get_user(message.from_user.id)
    if not user or user.role != "client":
        return
    await state.set_state(ClientStates.ai_chat)
    await _sticker(message, "travel")
    await message.answer(
        "✈️ Отлично, начинаем! Расскажите куда хотите, когда и сколько вас будет?\n\n"
        "Когда готовы — жмите <b>📋 Создать заявку</b> 🔥",
        reply_markup=ai_chat_kb(),
    )


@router.message(ClientStates.ai_chat, F.text == "🔙 В главное меню")
async def back_to_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню 🏠", reply_markup=client_menu())


@router.message(ClientStates.ai_chat, F.text == "📋 Создать заявку")
async def create_lead_btn(message: Message, state: FSMContext, bot: Bot) -> None:
    uid = message.from_user.id
    user = await get_user(uid)

    summary = get_chat_summary(uid)
    info = await extract_lead_info(uid)

    async with async_session() as s:
        lead = Lead(
            user_id=uid,
            summary=summary,
            country=info.get("country"),
            budget=info.get("budget"),
            dates=info.get("dates"),
            tour_type=info.get("tour_type"),
            status="new",
            ai_active=True,
        )
        s.add(lead)
        await s.commit()
        await s.refresh(lead)

    reset_ai_history(uid)
    await state.clear()

    await _sticker(message, "success")
    await message.answer(
        f"🎉 <b>Заявка №{lead.id} создана!</b>\n\n"
        "Менеджер уже получил её и скоро свяжется с вами! "
        "Скоро начнётся ваше путешествие мечты 🌍✨",
        reply_markup=client_menu(),
    )
    await _notify_managers(bot, lead, user)


@router.message(ClientStates.ai_chat, F.text)
async def ai_chat(message: Message, bot: Bot) -> None:
    uid = message.from_user.id
    await bot.send_chat_action(message.chat.id, "typing")
    reply = await get_ai_response(uid, message.text)
    await message.answer(reply)


# ── 🔥 Доступные туры ─────────────────────────────────────────────────────────

@router.message(F.text == "🔥 Доступные туры")
async def show_tours(message: Message) -> None:
    user = await get_user(message.from_user.id)
    if not user or user.role != "client":
        return
    async with async_session() as s:
        tours = (
            await s.execute(select(Tour).order_by(Tour.created_at.desc()))
        ).scalars().all()

    if not tours:
        await message.answer(
            "😔 Пока нет доступных туров.\nСовсем скоро добавим что-то крутое! 🌍"
        )
        return

    await _sticker(message, "travel")
    await message.answer(f"🔥 <b>Доступные туры ({len(tours)}):</b>")
    for tour in tours:
        await message.answer(
            f"🏝 <b>{tour.title}</b>\n"
            f"📍 Страна: {tour.country}\n"
            f"💰 Цена: {tour.price}\n"
            f"📅 Даты: {tour.dates}\n\n"
            f"📄 {tour.description}",
            reply_markup=tour_apply_kb(tour.id),
        )


@router.callback_query(F.data.startswith("tour_apply:"))
async def apply_from_tour(callback: CallbackQuery, bot: Bot) -> None:
    tour_id = int(callback.data.split(":")[1])
    uid = callback.from_user.id
    user = await get_user(uid)

    async with async_session() as s:
        tour = await s.get(Tour, tour_id)
        if not tour:
            await callback.answer("Тур не найден.", show_alert=True)
            return
        lead = Lead(
            user_id=uid,
            country=tour.country,
            tour_type="тур",
            summary=f"Клиент оставил заявку на тур: {tour.title}",
            status="new",
            ai_active=True,
            tour_id=tour_id,
        )
        s.add(lead)
        await s.commit()
        await s.refresh(lead)

    await callback.answer("✅ Заявка отправлена!")
    try:
        await callback.message.answer_sticker(get_sticker("success"))
    except Exception:
        pass
    await callback.message.answer(
        f"🎉 <b>Заявка №{lead.id} на тур «{tour.title}» создана!</b>\n\n"
        "Менеджер свяжется с вами в ближайшее время 🙌",
        reply_markup=client_menu(),
    )
    await _notify_managers(bot, lead, user)


# ── 📄 Мои заявки ─────────────────────────────────────────────────────────────

@router.message(F.text == "📄 Мои заявки")
async def my_leads(message: Message) -> None:
    user = await get_user(message.from_user.id)
    if not user or user.role != "client":
        return
    async with async_session() as s:
        leads = (
            await s.execute(
                select(Lead).where(Lead.user_id == message.from_user.id).order_by(Lead.created_at.desc())
            )
        ).scalars().all()

    if not leads:
        await message.answer("У вас пока нет заявок 🙈\nНажмите '🌍 Подобрать тур'!")
        return

    icons = {"new": "🆕", "in_progress": "🔄", "closed": "✅"}
    text = "📄 <b>Ваши заявки:</b>\n\n"
    for lead in leads:
        icon = icons.get(lead.status, "❓")
        country = f" · {lead.country}" if lead.country else ""
        text += f"{icon} Заявка <b>№{lead.id}</b>{country}\n📅 {lead.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    await message.answer(text)


# ── ⚙️ Настройки ──────────────────────────────────────────────────────────────

@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message) -> None:
    user = await get_user(message.from_user.id)
    if not user or user.role != "client":
        return
    lang_map = {"ru": "🇷🇺 Русский", "uz": "🇺🇿 O'zbekcha", "en": "🇬🇧 English"}
    await message.answer(
        f"⚙️ <b>Настройки</b>\n\n"
        f"👤 Имя: {user.name}\n"
        f"🎂 Возраст: {user.age or '—'}\n"
        f"📱 Телефон: {user.phone or '—'}\n"
        f"🌐 Язык: {lang_map.get(user.language, user.language)}\n\n"
        "Для изменения данных: /start",
    )



