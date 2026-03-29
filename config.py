import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ADMIN_IDS: list[int] = [2129061899]

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in .env")
