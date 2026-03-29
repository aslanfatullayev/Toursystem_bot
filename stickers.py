"""
Sticker file_ids organized by mood.
To get a sticker's file_id: forward it to @RawDataBot in Telegram.
Replace any ID here with your preferred stickers.
"""
import random

STICKERS: dict[str, list[str]] = {
    # Приветствие / Hello
    "hello": [
        "CAACAgIAAxkBAAIBbWVsFAABGqkAAUONmhI1OjCqq0oAAkEAA1KsyA1HAAFC1dWKCi4E",
        "CAACAgIAAxkBAAIBb2VsFAABpp7AAak2IIHZnlHVoHIAAkMCA1KsyA2K5EvBbNWk8i4E",
    ],
    # Ура / Celebration
    "celebrate": [
        "CAACAgIAAxkBAAIBcWVsFAAByJYAAYQyGj_yFKg6y4IAAh8AA1KsyA3ESUW9oJlV4C4E",
        "CAACAgIAAxkBAAIBc2VsFAABrJ8AAURq-hGcaBj7Fw0AAiUAA1KsyA3jXHBr-lMtCS4E",
    ],
    # Путешествие / Travel
    "travel": [
        "CAACAgIAAxkBAAIBdWVsFAABUKMAAWP0nYG8FaXsAY0AAisAA1KsyA1hAAFDxJz9_9guBi4E",
        "CAACAgIAAxkBAAIBd2VsFAABCKkAAX2MnzNh_V4mBNIAAjMAA1KsyA2zPLZVSrAmbi4E",
    ],
    # Ожидание / Loading
    "wait": [
        "CAACAgIAAxkBAAIBeWVsFAABiqsAAejGF_y57Tg-QHAAAJ4AA1KsyA3_2Zb5Ucp26S4E",
    ],
    # Успех / Success
    "success": [
        "CAACAgIAAxkBAAIBe2VsFAABCq0AAXm9r4yR6JLp03oAAoEAA1KsyA2QivE84XTUGS4E",
        "CAACAgIAAxkBAAIBfWVsFAABqq8AAVEiqk_e73VClCkAAo0AA1KsyA1IlBz5MLrk4S4E",
    ],
    # Грустно / Sad (для отказа)
    "thinking": [
        "CAACAgIAAxkBAAIBf2VsFAABkrEAAX5lPj2-jVCqbS8AApcAA1KsyA3kYG_u2CZ91C4E",
    ],
}


def get_sticker(mood: str) -> str:
    """Return a random sticker file_id for the given mood."""
    stickers = STICKERS.get(mood, STICKERS["hello"])
    return random.choice(stickers)
