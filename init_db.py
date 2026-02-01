import sqlite3
import os
# Удаляем старую базу, если есть
if os.path.exists("app/database.db"):
    os.remove("app/database.db")
# Создаем подключение
conn = sqlite3.connect("app/database.db")
cursor = conn.cursor()
# Создаем таблицу users
cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    task_description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
)
""")
# Создаем таблицу projects
cursor.execute("""
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT "discussion",
    client_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES users (id)
)
""")
# Создаем таблицу messages
cursor.execute("""
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    file_path TEXT,
    is_read BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id),
    FOREIGN KEY (sender_id) REFERENCES users (id)
)
""")
# Создаем таблицу transactions
cursor.execute("""
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    currency TEXT DEFAULT "RUB",
    status TEXT DEFAULT "pending",
    payment_method TEXT,
    yookassa_payment_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id)
)
""")
conn.commit()
conn.close()
print("Tables created successfully!")
# Проверяем
conn = sqlite3.connect("app/database.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:", [t[0] for t in tables])
conn.close()
