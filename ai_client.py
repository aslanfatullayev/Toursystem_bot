import json
import logging

from openai import AsyncOpenAI
from sqlalchemy import select

from config import OPENAI_API_KEY
from database import Tour, async_session, get_user
from prompts import SYSTEM_PROMPT

_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
_histories: dict[int, list[dict]] = {}
log = logging.getLogger(__name__)


async def _get_tours_context() -> str:
    """Load all tours from DB and format as text for the AI."""
    try:
        async with async_session() as s:
            tours = (await s.execute(select(Tour).order_by(Tour.country, Tour.title))).scalars().all()
        if not tours:
            return "Каталог туров пуст."
        lines = []
        for i, t in enumerate(tours, 1):
            lines.append(
                f"{i}. 🏷 {t.title} | 📍 {t.country} | 💰 {t.price} | 📅 {t.dates}\n"
                f"   📄 {t.description}"
            )
        return "\n\n".join(lines)
    except Exception as e:
        log.warning(f"Failed to load tours context: {e}")
        return "Каталог туров временно недоступен."


async def get_ai_response(user_id: int, user_message: str) -> str:
    user = await get_user(user_id)
    lang = user.language if user else "ru"
    lang_name = {"ru": "Russian", "uz": "Uzbek", "en": "English"}.get(lang, "Russian")

    if user_id not in _histories:
        _histories[user_id] = []
    history = _histories[user_id]
    history.append({"role": "user", "content": user_message})

    tours_context = await _get_tours_context()

    sys_msg = {
        "role": "system",
        "content": (
            SYSTEM_PROMPT
            + f"\n\nCRITICAL RULE: YOU MUST RESPOND EXCLUSIVELY IN {lang_name.upper()} LANGUAGE."
            + "\n\n## 🗂 КАТАЛОГ ТУРОВ (наши актуальные туры)\n\n"
            + "ВАЖНО: Ты должна рекомендовать ТОЛЬКО туры из этого каталога. "
            + "Не придумывай туры сама, не ссылайся на интернет. "
            + "Если подходящего тура нет — честно скажи об этом и предложи похожий из каталога.\n\n"
            + tours_context
        ),
    }

    try:
        resp = await _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[sys_msg] + history,
            temperature=0.7,
            max_tokens=1024,
        )
        reply = resp.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        history.pop()
        return f"⚠️ Ошибка AI: {e}"


async def extract_lead_info(user_id: int) -> dict:
    """Extract structured tour info from conversation history using AI."""
    history = _histories.get(user_id, [])
    if not history:
        return {}
    conversation = "\n".join(
        f"{'Клиент' if m['role'] == 'user' else 'Sofia'}: {m['content'][:300]}"
        for m in history[-12:]
    )
    try:
        resp = await _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract travel info from the conversation. "
                        "Return ONLY valid JSON with keys: country, budget, dates, tour_type. "
                        "Use null if not mentioned. No extra text."
                    ),
                },
                {"role": "user", "content": conversation},
            ],
            temperature=0,
            max_tokens=150,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        log.warning(f"extract_lead_info failed: {e}")
        return {}


def get_chat_summary(user_id: int) -> str:
    history = _histories.get(user_id, [])
    if not history:
        return "Нет данных"
    lines = []
    for m in history[-8:]:
        role = "Клиент" if m["role"] == "user" else "Sofia"
        lines.append(f"{role}: {m['content'][:200]}")
    return "\n".join(lines)


def reset_ai_history(user_id: int) -> None:
    _histories.pop(user_id, None)
