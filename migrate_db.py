import sqlite3

def migrate():
    print("Начинаем обновление базы данных...")
    conn = sqlite3.connect('aya_bot.db')
    c = conn.cursor()
    
    # Таблица users
    for col, ctype in [("age", "INTEGER"), ("phone", "VARCHAR(30)"), ("tg_username", "VARCHAR(100)")]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {ctype}")
            print(f"Добавлена колонка {col} в users")
        except sqlite3.OperationalError:
            print(f"Колонка {col} в users уже существует")

    # Таблица leads
    for col, ctype in [
        ("country", "VARCHAR(100)"), 
        ("budget", "VARCHAR(100)"), 
        ("dates", "VARCHAR(100)"), 
        ("tour_type", "VARCHAR(100)"), 
        ("tour_id", "INTEGER REFERENCES tours(id)")
    ]:
        try:
            c.execute(f"ALTER TABLE leads ADD COLUMN {col} {ctype}")
            print(f"Добавлена колонка {col} в leads")
        except sqlite3.OperationalError:
            print(f"Колонка {col} в leads уже существует")
            
    conn.commit()
    conn.close()
    print("✅ База данных успешно обновлена!")

if __name__ == "__main__":
    migrate()
