import sqlite3
import sys
def migrate_database():
    """Добавляет поле salt в таблицу users"""
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect('app/database.db')
        cursor = conn.cursor()
        # Проверяем, существует ли поле salt
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'salt' not in columns:
            print("Добавляем поле 'salt' в таблицу 'users'...")
            # Создаем временную таблицу с новым полем
            cursor.execute('''
                CREATE TABLE users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    salt VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Копируем данные из старой таблицы
            cursor.execute('''
                INSERT INTO users_new (id, email, name, hashed_password, created_at)
                SELECT id, email, name, hashed_password, created_at FROM users
            ''')
            # Удаляем старую таблицу и переименовываем новую
            cursor.execute('DROP TABLE users')
            cursor.execute('ALTER TABLE users_new RENAME TO users')
            print("Миграция успешно завершена!")
            # Для существующих пользователей генерируем соль
            cursor.execute("SELECT id, hashed_password FROM users WHERE salt IS NULL")
            users_without_salt = cursor.fetchall()
            import secrets
            for user_id, old_password in users_without_salt:
                # Генерируем случайную соль
                salt = secrets.token_hex(16)
                # Обновляем запись
                cursor.execute(
                    "UPDATE users SET salt = ?, hashed_password = ? WHERE id = ?",
                    (salt, old_password, user_id)
                )
            print(f"Обновлено {len(users_without_salt)} пользователей")
        else:
            print("Поле 'salt' уже существует в таблице 'users'")
        # Сохраняем изменения и закрываем соединение
        conn.commit()
        conn.close()
        print("Миграция базы данных завершена успешно!")
    except Exception as e:
        print(f"Ошибка при миграции: {e}")
        sys.exit(1)
if __name__ == "__main__":
    migrate_database()
