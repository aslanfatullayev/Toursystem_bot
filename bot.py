import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from config import TELEGRAM_BOT_TOKEN
from gemini_client import get_response, reset_session

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── Handlers ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the user sends /start."""
    user = update.effective_user
    name = user.first_name if user else "друг"

    welcome = (
        f"Привет, {name}! 👋 Я Айя — ваш персональный трэвел-консьерж.\n\n"
        "Помогу подобрать идеальный тур: пляжный отдых, горные приключения, "
        "городские экскурсии или экзотические направления — всё для вас! ✈️\n\n"
        "Куда хотите отправиться?"
    )
    await update.message.reply_text(welcome)


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear the conversation history for the current user."""
    user_id = update.effective_user.id
    reset_session(user_id)
    await update.message.reply_text(
        "История нашего разговора очищена 🔄 Начнём сначала!\n\nКуда хотите поехать?"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available commands."""
    text = (
        "📋 *Доступные команды:*\n\n"
        "/start — начать разговор\n"
        "/reset — очистить историю чата\n"
        "/help — показать эту справку\n\n"
        "Просто напишите мне куда хотите поехать — и я помогу подобрать тур! ✈️"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward user messages to Gemini AI and send back the response."""
    user_id = update.effective_user.id
    user_text = update.message.text

    # Show typing indicator while waiting for AI response
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",
    )

    logger.info(f"User {user_id}: {user_text!r}")

    # Run the blocking requests call in a thread pool so we don't block the event loop
    loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(None, get_response, user_id, user_text)

    logger.info(f"Aya -> User {user_id}: {reply[:80]!r}{'...' if len(reply) > 80 else ''}")

    try:
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception:
        # Fallback: send as plain text if Markdown parsing fails
        await update.message.reply_text(reply)



# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    """Start the Telegram bot."""
    logger.info("Starting Aya — Travel Concierge Bot...")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("help", cmd_help))

    # Register message handler (all text messages that are not commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
