"""
Diagnostic: показывает текущую модель бота и доступные модели OpenAI.
Run: python check_models.py
"""
from openai import OpenAI
from config import OPENAI_API_KEY

# Модель которую использует бот (должна совпадать с gemini_client.py)
BOT_MODEL = "gpt-4o-mini"

client = OpenAI(api_key=OPENAI_API_KEY)

print(f"🤖 Текущая модель бота: {BOT_MODEL}\n")

print("📋 Доступные модели GPT на вашем аккаунте:\n")
try:
    models = client.models.list()
    gpt_models = sorted(
        [m.id for m in models.data if "gpt" in m.id],
    )
    for m in gpt_models:
        marker = " ◄ (используется сейчас)" if m == BOT_MODEL else ""
        print(f"  • {m}{marker}")
except Exception as e:
    print(f"❌ Ошибка: {e}")
