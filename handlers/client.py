import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from ai_client import extract_lead_info, get_ai_response, get_chat_summary, reset_ai_history
from config import ADMIN_IDS
from database import Lead, Tour, User, async_session, get_user
from keyboards import (
    BTN_TOUR, BTN_AVAIL, BTN_MY, BTN_SETTINGS, BTN_CREATE, BTN_MENU,
    ai_chat_kb, change_lang_kb, client_menu, lead_actions_kb, tour_apply_kb
)
from states import ClientStates
from stickers import get_sticker

router = Router()
log = logging.getLogger(__name__)

_TEXTS = {
    "start_chat": {
        "ru": "✈️ Отлично, начинаем! Расскажите куда хотите, когда и сколько вас будет?\n\nКогда готовы — жмите <b>📋 Создать заявку</b> 🔥",
        "uz": "✈️ Ajoyib, boshladik! Qayerga, qachon va necha kishi bo'lishingizni aytib bering?\n\nTayyor bo'lsangiz — <b>📋 Ariza yaratish</b> tugmasini bosing 🔥",
        "en": "✈️ Great, let's start! Tell me where, when, and how many people?\n\nWhen ready - press <b>📋 Create request</b> 🔥"
    },
    "main_menu": {
        "ru": "Главное меню 🏠",
        "uz": "Asosiy menyu 🏠",
        "en": "Main menu 🏠"
    },
    "lead_created": {
        "ru": "🎉 <b>Заявка №{lead_id} создана!</b>\n\nМенеджер уже получил её и скоро свяжется с вами! Скоро начнётся ваше путешествие мечты 🌍✨",
        "uz": "🎉 <b>№{lead_id} ariza yaratildi!</b>\n\nMenejer uni qabul qildi va tez orada siz bilan bog'lanadi! Orzuyingizdagi sayohat tez orada boshlanadi 🌍✨",
        "en": "🎉 <b>Request №{lead_id} created!</b>\n\nA manager has received it and will contact you soon! Your dream journey begins soon 🌍✨"
    },
    "no_tours": {
        "ru": "😔 Пока нет доступных туров.\nСовсем скоро добавим что-то крутое! 🌍",
        "uz": "😔 Hozircha mavjud turlar yo'q.\nTez orada ajoyib narsalar qo'shamiz! 🌍",
        "en": "😔 No available tours right now.\nWe will add something awesome very soon! 🌍"
    },
    "tours_list": {
        "ru": "🔥 <b>Доступные туры ({count}):</b>",
        "uz": "🔥 <b>Mavjud turlar ({count}):</b>",
        "en": "🔥 <b>Available tours ({count}):</b>"
    },
    "tour_apply_toast": {
        "ru": "✅ Заявка отправлена!",
        "uz": "✅ Ariza yuborildi!",
        "en": "✅ Request sent!"
    },
    "tour_lead_created": {
        "ru": "🎉 <b>Заявка №{lead_id} на тур «{tour_title}» создана!</b>\n\nМенеджер свяжется с вами в ближайшее время 🙌",
        "uz": "🎉 <b>«{tour_title}» turi uchun №{lead_id} ariza yaratildi!</b>\n\nMenejer tez orada siz bilan bog'lanadi 🙌",
        "en": "🎉 <b>Request №{lead_id} for tour «{tour_title}» created!</b>\n\nA manager will contact you shortly 🙌"
    },
    "no_leads": {
        "ru": "У вас пока нет заявок 🙈\nНажмите '🌍 Подобрать тур'!",
        "uz": "Sizda hozircha arizalar yo'q 🙈\nTur tanlash tugmasini bosing!",
        "en": "You don't have any requests yet 🙈\nPress the find a tour button!"
    },
    "my_leads": {
        "ru": "📄 <b>Ваши заявки:</b>\n\n",
        "uz": "📄 <b>Sizning arizalaringiz:</b>\n\n",
        "en": "📄 <b>Your requests:</b>\n\n"
    },
    "settings": {
        "ru": "⚙️ <b>Настройки</b>\n\n👤 Имя: {name}\n🎂 Возраст: {age}\n📱 Телефон: {phone}\n🌐 Язык: {lang}\n\nДля перерегистрации: /start\nДля смены языка нажмите кнопку ниже:",
        "uz": "⚙️ <b>Sozlamalar</b>\n\n👤 Ism: {name}\n🎂 Yosh: {age}\n📱 Telefon: {phone}\n🌐 Til: {lang}\n\nQaytadan ro'yxatdan o'tish uchun: /start\nTilni o'zgartirish uchun quyidagi tugmani bosing:",
        "en": "⚙️ <b>Settings</b>\n\n👤 Name: {name}\n🎂 Age: {age}\n📱 Phone: {phone}\n🌐 Language: {lang}\n\nTo re-register: /start\nTo change language, press the button below:"
    }
}


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

@router.message(F.text.in_(BTN_TOUR.values()))
async def start_chat(message: Message, state: FSMContext) -> None:
    user = await get_user(message.from_user.id)
    if not user or user.role != "client":
        return
    await state.set_state(ClientStates.ai_chat)
    await _sticker(message, "travel")
    await message.answer(
        _TEXTS["start_chat"][user.language],
        reply_markup=ai_chat_kb(user.language),
    )


@router.message(ClientStates.ai_chat, F.text.in_(BTN_MENU.values()))
async def back_to_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await get_user(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(_TEXTS["main_menu"][lang], reply_markup=client_menu(lang))


@router.message(ClientStates.ai_chat, F.text.in_(BTN_CREATE.values()))
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
        _TEXTS["lead_created"][user.language].format(lead_id=lead.id),
        reply_markup=client_menu(user.language),
    )
    await _notify_managers(bot, lead, user)


@router.message(ClientStates.ai_chat, F.text)
async def ai_chat(message: Message, bot: Bot) -> None:
    uid = message.from_user.id
    await bot.send_chat_action(message.chat.id, "typing")
    reply = await get_ai_response(uid, message.text)
    await message.answer(reply)


# ── 🔥 Доступные туры ─────────────────────────────────────────────────────────

@router.message(F.text.in_(BTN_AVAIL.values()))
async def show_tours(message: Message) -> None:
    user = await get_user(message.from_user.id)
    if not user or user.role != "client":
        return
    async with async_session() as s:
        tours = (
            await s.execute(select(Tour).order_by(Tour.created_at.desc()))
        ).scalars().all()

    if not tours:
        await message.answer(_TEXTS["no_tours"][user.language])
        return

    await _sticker(message, "travel")
    await message.answer(_TEXTS["tours_list"][user.language].format(count=len(tours)))
    for tour in tours:
        await message.answer(
            f"🏝 <b>{tour.title}</b>\n"
            f"📍 {tour.country}\n"
            f"💰 {tour.price}\n"
            f"📅 {tour.dates}\n\n"
            f"📄 {tour.description}",
            reply_markup=tour_apply_kb(tour.id),
        )


@router.callback_query(F.data.startswith("tour_apply:"))
async def apply_from_tour(callback: CallbackQuery, bot: Bot) -> None:
    tour_id = int(callback.data.split(":")[1])
    uid = callback.from_user.id
    user = await get_user(uid)
    lang = user.language if user else "ru"

    async with async_session() as s:
        tour = await s.get(Tour, tour_id)
        if not tour:
            await callback.answer("Error", show_alert=True)
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

    await callback.answer(_TEXTS["tour_apply_toast"][lang])
    try:
        await callback.message.answer_sticker(get_sticker("success"))
    except Exception:
        pass
    await callback.message.answer(
        _TEXTS["tour_lead_created"][lang].format(lead_id=lead.id, tour_title=tour.title),
        reply_markup=client_menu(lang),
    )
    await _notify_managers(bot, lead, user)


# ── 📄 Мои заявки ─────────────────────────────────────────────────────────────

@router.message(F.text.in_(BTN_MY.values()))
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
        await message.answer(_TEXTS["no_leads"][user.language])
        return

    icons = {"new": "🆕", "in_progress": "🔄", "closed": "✅"}
    text = _TEXTS["my_leads"][user.language]
    for lead in leads:
        icon = icons.get(lead.status, "❓")
        country = f" · {lead.country}" if lead.country else ""
        text += f"{icon} №{lead.id}{country}\n📅 {lead.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    await message.answer(text)


# ── ⚙️ Настройки ──────────────────────────────────────────────────────────────

@router.message(F.text.in_(BTN_SETTINGS.values()))
async def settings(message: Message) -> None:
    user = await get_user(message.from_user.id)
    if not user or user.role != "client":
        return
    lang_map = {"ru": "🇷🇺 Русский", "uz": "🇺🇿 O'zbekcha", "en": "🇬🇧 English"}
    await message.answer(
        _TEXTS["settings"][user.language].format(
            name=user.name,
            age=user.age or '—',
            phone=user.phone or '—',
            lang=lang_map.get(user.language, user.language)
        ),
        reply_markup=change_lang_kb(),
    )


@router.callback_query(F.data.startswith("change_lang:"))
async def process_change_lang(callback: CallbackQuery) -> None:
    lang = callback.data.split(":")[1]
    uid = callback.from_user.id
    async with async_session() as s:
        user = await s.get(User, uid)
        if user:
            user.language = lang
            await s.commit()

    msg_map = {
        "ru": "✅ Язык успешно изменён!",
        "uz": "✅ Til muvaffaqiyatli o'zgartirildi!",
        "en": "✅ Language successfully changed!"
    }
    await callback.answer(msg_map.get(lang, "OK"))
    await callback.message.delete()
    await callback.message.answer(msg_map.get(lang, "OK"), reply_markup=client_menu(lang))
