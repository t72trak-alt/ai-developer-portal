from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env

print("\n" + "="*60)
print("🔍 ДИАГНОСТИКА ПОДКЛЮЧЕНИЯ К БД")
print("="*60)

# Текущая рабочая директория
current_dir = os.getcwd()
print(f"📁 Текущая рабочая директория: {current_dir}")

# Путь к этому файлу (database.py)
current_file = os.path.abspath(__file__)
print(f"📁 Этот файл: {current_file}")

# Определяем абсолютный путь к БД (ищем app.db в корне проекта)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"📁 BASE_DIR (корень проекта): {BASE_DIR}")

# Проверяем наличие app.db в разных местах
possible_paths = [
    os.path.join(BASE_DIR, "app.db"),
    os.path.join(current_dir, "app.db"),
    os.path.abspath("app.db")
]

for i, path in enumerate(possible_paths):
    exists = os.path.exists(path)
    print(f"📁 Вариант {i+1}: {path} - {'✅ СУЩЕСТВУЕТ' if exists else '❌ НЕТ'}")

# Используем первый существующий путь
DB_PATH = None
for path in possible_paths:
    if os.path.exists(path):
        DB_PATH = path
        print(f"✅ ВЫБРАН: {DB_PATH}")
        break

if not DB_PATH:
    DB_PATH = possible_paths[0]  # По умолчанию первый вариант
    print(f"⚠️ Ни один файл не найден, создадим: {DB_PATH}")

# Получаем URL БД из переменных окружения или используем найденный путь
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    print(f"📁 ИТОГОВЫЙ ПУТЬ К БД: {DB_PATH}")
    print(f"📁 DATABASE_URL: {DATABASE_URL}")

# Создаем движок SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    # Для SQLite нужно добавить connect_args
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# !!! ВАЖНО: СОЗДАЁМ ТАБЛИЦЫ АВТОМАТИЧЕСКИ !!!
# Импортируем модели, чтобы они были зарегистрированы в Base
from app.models import User, Message, ClientDetails, Project, Transaction, Payment
# Создаём все таблицы, если их ещё нет
Base.metadata.create_all(bind=engine)
print("✅ Таблицы БД созданы/проверены")

print("="*60 + "\n")

# Функция для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()