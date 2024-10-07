import sqlite3

# Подключение к базе данных
db = sqlite3.connect('database.db')

databaseCursor = db.cursor()

databaseCursor.execute("""CREATE TABLE events (
    summary text,
    description text,
    start text,
    end text,
    location text
)""")

# Обновить базу данных
db.commit()

# Закрытие базы данных
db.close()