from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS
from database import create_user, get_user
from keyboards import admin_menu, client_menu, language_kb, manager_menu, phone_kb, skip_kb
from states import Registration
from stickers import get_sticker

router = Router()

_TEXTS = {
    "name_prompt": {
        "ru": "Как вас зовут? 😊",
        "uz": "Ismingiz nima? 😊",
        "en": "What's your name? 😊",
    },
    "age_prompt": {
        "ru": "Сколько вам лет? 🎂",
        "uz": "Yoshingiz necha? 🎂",
        "en": "How old are you? 🎂",
    },
    "phone_prompt": {
        "ru": "Отправьте ваш номер телефона 📱\n(нажмите кнопку или введите вручную)",
        "uz": "Telefon raqamingizni yuboring 📱\n(tugmani bosing yoki qo'lda kiriting)",
        "en": "Share your phone number 📱\n(press the button or type manually)",
    },
    "username_prompt": {
        "ru": "Ваш Telegram username? (например: @username)\nЕсли нет — нажмите «Пропустить»",
        "uz": "Telegram usernamingiz? (masalan: @username)\nYo'q bo'lsa — «Pропустить» bosing",
        "en": "Your Telegram username? (e.g. @username)\nIf none — press Skip",
    },
    "done": {
        "ru": "🎉 Регистрация завершена!\n\nПривет, <b>{name}</b>! Я — София, ваш трэвел-консьерж.\nКуда мечтаете поехать? ✈️",
        "uz": "🎉 Ro'yxatdan o'tish yakunlandi!\n\nSalom, <b>{name}</b>! Men — Sofia, sizning travel-konsyerj.\nQayerga borishni orzu qilyapsiz? ✈️",
        "en": "🎉 Registration complete!\n\nHey <b>{name}</b>! I'm Sofia, your travel concierge.\nWhere do you dream of going? ✈️",
    },
}


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    uid = message.from_user.id

    if uid in ADMIN_IDS:
        await message.answer("👑 <b>Добро пожаловать, Администратор!</b>", reply_markup=admin_menu())
        return

    user = await get_user(uid)
    if user:
        if user.role == "manager":
            await message.answer(f"💼 Salom / Привет, <b>{user.name}</b>!", reply_markup=manager_menu())
        else:
            try:
                await message.answer_sticker(get_sticker("hello"))
            except Exception:
                pass
            await message.answer(f"👋 С возвращением, <b>{user.name}</b>! 🌟", reply_markup=client_menu())
        return

    try:
        await message.answer_sticker(get_sticker("hello"))
    except Exception:
        pass
    await message.answer(
        "👋 Добро пожаловать в <b>Sofia Travel</b>!\nXush kelibsiz!\n\n"
        "🌐 Выберите язык / Tilni tanlang / Choose language:",
        reply_markup=language_kb(),
    )
    await state.set_state(Registration.language)


@router.callback_query(Registration.language, F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery, state: FSMContext) -> None:
    lang = callback.data.split(":")[1]
    await state.update_data(language=lang)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(_TEXTS["name_prompt"][lang])
    await callback.answer()
    await state.set_state(Registration.name)


@router.message(Registration.name, F.text)
async def set_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("language", "ru")
    name = message.text.strip()[:50]
    await state.update_data(name=name)
    await message.answer(_TEXTS["age_prompt"][lang])
    await state.set_state(Registration.age)


@router.message(Registration.age, F.text)
async def set_age(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("language", "ru")
    age_text = message.text.strip()
    age = int(age_text) if age_text.isdigit() and 1 <= int(age_text) <= 120 else None
    await state.update_data(age=age)
    await message.answer(_TEXTS["phone_prompt"][lang], reply_markup=phone_kb())
    await state.set_state(Registration.phone)


@router.message(Registration.phone, F.contact)
async def set_phone_contact(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    data = await state.get_data()
    lang = data.get("language", "ru")
    await message.answer(_TEXTS["username_prompt"][lang], reply_markup=skip_kb())
    await state.set_state(Registration.tg_username)


@router.message(Registration.phone, F.text)
async def set_phone_text(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    await state.update_data(phone=phone)
    data = await state.get_data()
    lang = data.get("language", "ru")
    await message.answer(_TEXTS["username_prompt"][lang], reply_markup=skip_kb())
    await state.set_state(Registration.tg_username)


@router.message(Registration.tg_username, F.text)
async def set_username(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("language", "ru")
    raw = message.text.strip()
    tg_username = None if raw == "➡️ Пропустить" else raw.lstrip("@")

    # Auto-fill from Telegram profile if available
    if tg_username is None and message.from_user.username:
        tg_username = message.from_user.username

    await create_user(
        user_id=message.from_user.id,
        name=data["name"],
        language=lang,
        age=data.get("age"),
        phone=data.get("phone"),
        tg_username=tg_username,
    )
    await state.clear()

    try:
        await message.answer_sticker(get_sticker("celebrate"))
    except Exception:
        pass
    await message.answer(_TEXTS["done"][lang].format(name=data["name"]), reply_markup=client_menu())
