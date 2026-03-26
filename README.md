# 🌍 Aya — AI Travel Concierge Telegram Bot

Telegram-бот на Python с интеграцией **Google Gemini AI**.  
Бот выступает как **Айя** — персональный трэвел-консьерж международного турагентства.

---

## 📁 Структура проекта

```
Toursystem_bot/
├── bot.py              # Точка входа, Telegram-хендлеры
├── gemini_client.py    # Клиент Gemini AI (история per-user)
├── prompts.py          # Системный промпт Айи
├── config.py           # Загрузка переменных окружения
├── requirements.txt    # Зависимости
├── .env.example        # Шаблон .env
└── .gitignore
```

---

## ⚙️ Установка и запуск

### 1. Клонируйте репозиторий

```bash
git clone <url>
cd Toursystem_bot
```

### 2. Создайте виртуальное окружение (рекомендуется)

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Настройте переменные окружения

Скопируйте `.env.example` в `.env` и вставьте ваши ключи:

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

Откройте `.env` и заполните:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
GEMINI_API_KEY=ваш_ключ_от_Google_AI_Studio
```

> **Где получить ключи:**
> - **Telegram Token** → [@BotFather](https://t.me/BotFather) → `/newbot`
> - **Gemini API Key** → [aistudio.google.com](https://aistudio.google.com/app/apikey)

### 5. Запустите бота

```bash
python bot.py
```

---

## 🤖 Команды бота

| Команда  | Описание                         |
|----------|----------------------------------|
| `/start` | Приветствие и начало разговора   |
| `/reset` | Очистить историю чата            |
| `/help`  | Список команд                    |

---

## 🧠 Как работает бот

1. Пользователь пишет сообщение
2. Бот передаёт его в **Gemini AI** с системным промптом Айи
3. История диалога сохраняется в памяти (per-user)
4. Бот отвечает строго в рамках туризма
5. При `/reset` история очищается — новый диалог с нуля

---

## 🚫 Важно

- Файл `.env` **не коммитить** в Git (он в `.gitignore`)
- Цены в боте — **ориентировочные**, финальные уточняет менеджер