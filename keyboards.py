from aiogram.types import (
    InlineKeyboardMarkup, KeyboardButton,
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# ── Translations ───────────────────────────────────────────────────────────────

BTN_TOUR = {"ru": "🌍 Подобрать тур", "uz": "🌍 Tur tanlash", "en": "🌍 Find a tour"}
BTN_AVAIL = {"ru": "🔥 Доступные туры", "uz": "🔥 Mavjud turlar", "en": "🔥 Available tours"}
BTN_MY = {"ru": "📄 Мои заявки", "uz": "📄 Mening arizalarim", "en": "📄 My requests"}
BTN_SETTINGS = {"ru": "⚙️ Настройки", "uz": "⚙️ Sozlamalar", "en": "⚙️ Settings"}

BTN_CREATE = {"ru": "📋 Создать заявку", "uz": "📋 Ariza yaratish", "en": "📋 Create request"}
BTN_MENU = {"ru": "🔙 В главное меню", "uz": "🔙 Asosiy menyuga", "en": "🔙 Main menu"}

BTN_CONTACT = {"ru": "📱 Отправить контакт", "uz": "📱 Kontakt yuborish", "en": "📱 Share contact"}
BTN_SKIP = {"ru": "➡️ Пропустить", "uz": "➡️ O'tkazib yuborish", "en": "➡️ Skip"}

def _t(btn_dict: dict, lang: str) -> str:
    return btn_dict.get(lang, btn_dict["ru"])


# ── Reply menus ────────────────────────────────────────────────────────────────

def client_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=_t(BTN_TOUR, lang))
    b.button(text=_t(BTN_AVAIL, lang))
    b.button(text=_t(BTN_MY, lang))
    b.button(text=_t(BTN_SETTINGS, lang))
    b.adjust(2, 2)
    return b.as_markup(resize_keyboard=True)


def manager_menu() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text="📥 Новые заявки")
    b.button(text="📊 Все мои заявки")
    b.button(text="🏝 Туры")
    b.adjust(2, 1)
    return b.as_markup(resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text="➕ Добавить менеджера")
    b.button(text="➖ Удалить менеджера")
    b.button(text="📊 Все заявки")
    b.button(text="👥 Пользователи")
    b.button(text="🏝 Туры")
    b.adjust(2, 2, 1)
    return b.as_markup(resize_keyboard=True)


def ai_chat_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=_t(BTN_CREATE, lang))
    b.button(text=_t(BTN_MENU, lang))
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)


def phone_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=_t(BTN_CONTACT, lang), request_contact=True)
    return b.as_markup(resize_keyboard=True, one_time_keyboard=True)


def skip_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=_t(BTN_SKIP, lang))
    return b.as_markup(resize_keyboard=True, one_time_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text="❌ Отмена")
    return b.as_markup(resize_keyboard=True)


def back_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text="🔙 Назад")
    return b.as_markup(resize_keyboard=True)


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


# ── Inline keyboards ───────────────────────────────────────────────────────────

def language_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🇷🇺 Русский", callback_data="lang:ru")
    b.button(text="🇺🇿 O'zbekcha", callback_data="lang:uz")
    b.button(text="🇬🇧 English", callback_data="lang:en")
    b.adjust(1)
    return b.as_markup()


def change_lang_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🇷🇺 Русский", callback_data="change_lang:ru")
    b.button(text="🇺🇿 O'zbekcha", callback_data="change_lang:uz")
    b.button(text="🇬🇧 English", callback_data="change_lang:en")
    b.adjust(3)
    return b.as_markup()


def lead_actions_kb(lead_id: int, client_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Взять в работу", callback_data=f"take:{lead_id}:{client_id}")
    b.adjust(1)
    return b.as_markup()


def tour_apply_kb(tour_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📋 Оставить заявку", callback_data=f"tour_apply:{tour_id}")
    return b.as_markup()


def countries_kb(countries: list[str]) -> InlineKeyboardMarkup:
    """Show list of unique countries as buttons."""
    b = InlineKeyboardBuilder()
    for country in sorted(countries):
        b.button(text=f"📍 {country}", callback_data=f"country:{country}")
    b.adjust(2)
    return b.as_markup()


def tours_list_kb(tours: list, country: str) -> InlineKeyboardMarkup:
    """Show tours for a specific country."""
    b = InlineKeyboardBuilder()
    for tour in tours:
        b.button(text=f"✈️ {tour.title}", callback_data=f"tour_detail:{tour.id}")
    b.button(text="🔙 К странам", callback_data="tours_back_countries")
    b.adjust(1)
    return b.as_markup()


def tour_detail_kb(tour_id: int, country: str) -> InlineKeyboardMarkup:
    """Show apply button + back button for a single tour."""
    b = InlineKeyboardBuilder()
    b.button(text="📋 Оставить заявку", callback_data=f"tour_apply:{tour_id}")
    b.button(text="🔙 Назад к турам", callback_data=f"country:{country}")
    b.adjust(1)
    return b.as_markup()
