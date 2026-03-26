from openai import OpenAI
from config import OPENAI_API_KEY
from prompts import SYSTEM_PROMPT

# OpenAI client
_client = OpenAI(api_key=OPENAI_API_KEY)

# In-memory chat history per user: user_id -> list of OpenAI message dicts
_histories: dict[int, list] = {}

# System prompt message (injected once at start of each session)
_SYSTEM_MESSAGE = {"role": "system", "content": SYSTEM_PROMPT}


def get_response(user_id: int, user_message: str) -> str:
    """
    Send a message and return Aya's reply.
    Maintains per-user conversation history using OpenAI Chat API.
    """
    if user_id not in _histories:
        _histories[user_id] = []

    history = _histories[user_id]

    # Append the new user message
    history.append({"role": "user", "content": user_message})

    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[_SYSTEM_MESSAGE] + history,
            temperature=0.7,
            max_tokens=1024,
        )

        reply_text = response.choices[0].message.content

        # Save assistant reply to history
        history.append({"role": "assistant", "content": reply_text})

        return reply_text

    except Exception as e:
        # Roll back the unsaved user message
        history.pop()
        return f"⚠️ Произошла ошибка: {e}"


def reset_session(user_id: int) -> None:
    """Delete the chat history for the given user."""
    _histories.pop(user_id, None)
