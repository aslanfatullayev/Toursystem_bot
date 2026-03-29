import json
import logging

from openai import AsyncOpenAI

from config import OPENAI_API_KEY
from prompts import SYSTEM_PROMPT

_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
_histories: dict[int, list[dict]] = {}
_SYSTEM_MSG = {"role": "system", "content": SYSTEM_PROMPT}
log = logging.getLogger(__name__)


async def get_ai_response(user_id: int, user_message: str) -> str:
    if user_id not in _histories:
        _histories[user_id] = []
    history = _histories[user_id]
    history.append({"role": "user", "content": user_message})
    try:
        resp = await _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[_SYSTEM_MSG] + history,
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
