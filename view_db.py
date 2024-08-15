import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM payments")
rows = cursor.fetchall()

if rows:
    print("Содержание таблицы payments:")
    for row in rows:
        print(f"User ID: {row[0]}")
else:
    print("Таблица payments пуста")

conn.close()