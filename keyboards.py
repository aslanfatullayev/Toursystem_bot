from aiogram.types import (
    InlineKeyboardMarkup, KeyboardButton,
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ── Reply menus ────────────────────────────────────────────────────────────────

def client_menu() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text="🌍 Подобрать тур")
    b.button(text="🔥 Доступные туры")
    b.button(text="📄 Мои заявки")
    b.button(text="⚙️ Настройки")
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


def ai_chat_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text="📋 Создать заявку")
    b.button(text="🔙 В главное меню")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)


def phone_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text="📱 Отправить контакт", request_contact=True)
    return b.as_markup(resize_keyboard=True, one_time_keyboard=True)


def skip_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text="➡️ Пропустить")
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


def lead_actions_kb(lead_id: int, client_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Взять в работу", callback_data=f"take:{lead_id}:{client_id}")
    b.adjust(1)
    return b.as_markup()


def tour_apply_kb(tour_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📋 Оставить заявку", callback_data=f"tour_apply:{tour_id}")
    return b.as_markup()
