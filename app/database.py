from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загружаем переменные из .env (для локальной разработки)
load_dotenv()

# ========== ЖЁСТКАЯ ДИАГНОСТИКА ==========
logger.info("!"*60)
logger.info("!!! ЖЁСТКАЯ ДИАГНОСТИКА ПЕРЕМЕННЫХ !!!")
logger.info("!"*60)

# Проверяем через разные методы
logger.info("1. ЧЕРЕЗ os.environ.get():")
logger.info(f"DATABASE_URL: {os.environ.get('DATABASE_URL')}")
logger.info(f"NEON_DATABASE_URL: {os.environ.get('NEON_DATABASE_URL')}")

logger.info("2. ЧЕРЕЗ os.getenv():")
logger.info(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
logger.info(f"NEON_DATABASE_URL: {os.getenv('NEON_DATABASE_URL')}")

logger.info("3. ВСЕ ПЕРЕМЕННЫЕ (первые 20):")
count = 0
for key, value in os.environ.items():
    if count < 20:
        logger.info(f"  {key}={value[:30] if value else ''}...")
    count += 1

logger.info("4. ПРОВЕРКА НАЛИЧИЯ КЛЮЧЕЙ:")
logger.info(f"'DATABASE_URL' in os.environ: {'DATABASE_URL' in os.environ}")
logger.info(f"'NEON_DATABASE_URL' in os.environ: {'NEON_DATABASE_URL' in os.environ}")

logger.info("!"*60)
# ==========================================

logger.info("="*60)
logger.info("🔍 ДИАГНОСТИКА ПОДКЛЮЧЕНИЯ К БД")
logger.info("="*60)

# Диагностика окружения
logger.info(f"📌 Python версия: {sys.version}")
logger.info(f"📌 Текущая директория: {os.getcwd()}")
logger.info(f"📌 Файл: {__file__}")

# Проверяем все переменные окружения (только имена, для безопасности)
env_vars = [key for key in os.environ.keys() if not key.startswith('_')]
logger.info(f"📌 Доступные переменные окружения: {env_vars}")

# Получаем URL БД из переменных окружения (приоритет!)
# Сначала проверяем DATABASE_URL (стандартная для Railway)
DATABASE_URL = os.environ.get("DATABASE_URL")

# Если нет, проверяем другие возможные имена
if not DATABASE_URL:
    DATABASE_URL = os.environ.get("NEON_DATABASE_URL")
    if DATABASE_URL:
        logger.info("✅ Найдена NEON_DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = os.environ.get("POSTGRES_URL")
    if DATABASE_URL:
        logger.info("✅ Найдена POSTGRES_URL")

if not DATABASE_URL:
    DATABASE_URL = os.getenv("DATABASE_URL")  # Пробуем через getenv как запасной вариант

# Выводим информацию о найденной переменной
if DATABASE_URL:
    # Маскируем URL для безопасности (показываем только хост и базу)
    masked_url = DATABASE_URL
    if '@' in DATABASE_URL:
        parts = DATABASE_URL.split('@')
        credentials = parts[0].split(':')
        if len(credentials) >= 2:
            masked_url = f"{credentials[0]}:***@{parts[1]}"
        else:
            masked_url = f"***@{parts[1]}"
    logger.info(f"✅ DATABASE_URL найдена: {masked_url}")
    
    # Проверяем протокол
    if DATABASE_URL.startswith("postgres://"):
        logger.info("⚠️ Обнаружен протокол postgres://, меняем на postgresql://")
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        logger.info(f"✅ Исправлено на: {DATABASE_URL.split('@')[0].split(':')[0]}:***@{DATABASE_URL.split('@')[-1]}")
else:
    logger.info("❌ DATABASE_URL НЕ НАЙДЕНА в окружении")

# Если есть DATABASE_URL и это PostgreSQL — используем его
if DATABASE_URL and ("postgresql" in DATABASE_URL or "postgres" in DATABASE_URL):
    logger.info("✅ Используется PostgreSQL")
    
    # Добавляем sslmode=require если его нет (для Neon.tech)
    if "sslmode" not in DATABASE_URL:
        if "?" in DATABASE_URL:
            DATABASE_URL += "&sslmode=require"
        else:
            DATABASE_URL += "?sslmode=require"
        logger.info("✅ Добавлен параметр sslmode=require")
    
    try:
        # Создаем engine для PostgreSQL
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False,  # Поставьте True для отладки SQL
            connect_args={
                "connect_timeout": 10,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5
            }
        )
        
        # Проверяем подключение
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
            logger.info("✅ Подключение к PostgreSQL проверено (SELECT 1 успешен)")
            
            # Получаем версию PostgreSQL
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✅ PostgreSQL версия: {version[:50]}...")
            
    except Exception as e:
        logger.info(f"❌ Ошибка подключения к PostgreSQL: {e}")
        logger.info("⚠️ Переключаемся на SQLite как запасной вариант")
        DATABASE_URL = None  # Принудительно переключаемся на SQLite
        # Создаем engine для SQLite
        sqlite_path = "/app/app.db"
        logger.info(f"📁 Используем SQLite: {sqlite_path}")
        engine = create_engine(
            f"sqlite:///{sqlite_path}",
            connect_args={"check_same_thread": False}
        )
        
else:
    # Если нет DATABASE_URL или ошибка — используем SQLite
    logger.info("⚠️ Используем SQLite (локальная разработка)")
    
    # Текущая рабочая директория
    current_dir = os.getcwd()
    logger.info(f"📁 Текущая рабочая директория: {current_dir}")
    
    # Путь к этому файлу (database.py)
    current_file = os.path.abspath(__file__)
    logger.info(f"📁 Этот файл: {current_file}")
    
    # Определяем абсолютный путь к БД (ищем app.db в корне проекта)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logger.info(f"📁 BASE_DIR (корень проекта): {BASE_DIR}")
    
    # Проверяем наличие app.db в разных местах
    possible_paths = [
        os.path.join(BASE_DIR, "app.db"),
        os.path.join(current_dir, "app.db"),
        os.path.abspath("app.db"),
        "/app/app.db",  # Путь в контейнере Railway
    ]
    
    for i, path in enumerate(possible_paths):
        exists = os.path.exists(path)
        logger.info(f"📁 Вариант {i+1}: {path} - {'✅ СУЩЕСТВУЕТ' if exists else '❌ НЕТ'}")
    
    # Используем первый существующий путь
    DB_PATH = None
    for path in possible_paths:
        if os.path.exists(path):
            DB_PATH = path
            logger.info(f"✅ ВЫБРАН: {DB_PATH}")
            break
    
    if not DB_PATH:
        DB_PATH = possible_paths[0]  # По умолчанию первый вариант
        logger.info(f"⚠️ Ни один файл не найден, создадим: {DB_PATH}")
    
    # Формируем URL для SQLite
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    logger.info(f"📁 ИТОГОВЫЙ ПУТЬ К БД: {DB_PATH}")
    logger.info(f"📁 DATABASE_URL: {DATABASE_URL}")
    
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

logger.info("="*60)
logger.info("🔄 СОЗДАНИЕ ТАБЛИЦ...")
logger.info("="*60)

# ========== ДОБАВЛЕННЫЕ ФУНКЦИИ ==========

def create_tables():
    """Создает все таблицы, если они не существуют"""
    logger.info("🔄 ВЫЗВАНА create_tables()")
    try:
        # Импортируем модели, чтобы они были зарегистрированы в Base
        from app.models import User, Message, ClientDetails, Project, Transaction, Payment
        
        # Создаём все таблицы, если их ещё нет
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Таблицы БД созданы/проверены")
        
        # Дополнительная проверка для PostgreSQL
        if "postgresql" in str(engine.url):
            with engine.connect() as conn:
                # Проверяем, какие таблицы созданы
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in result]
                logger.info(f"📊 Таблицы в PostgreSQL: {tables}")
        return True
    except Exception as e:
        logger.info(f"❌ Ошибка при создании таблиц: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_connection():
    """Проверяет подключение к базе данных"""
    logger.info("🔄 ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БД...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
            
            # Определяем тип БД
            if "postgresql" in str(engine.url):
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"✅ PostgreSQL подключен: {version[:50]}...")
            else:
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.scalar()
                logger.info(f"✅ SQLite подключен: версия {version}")
            
            return True
    except Exception as e:
        logger.info(f"❌ Ошибка подключения к БД: {e}")
        return False

# ==========================================

# Вызываем создание таблиц при импорте модуля
try:
    # Импортируем модели, чтобы они были зарегистрированы в Base
    from app.models import User, Message, ClientDetails, Project, Transaction, Payment
    
    # Создаём все таблицы, если их ещё нет
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Таблицы БД созданы/проверены")
    
    # Дополнительная проверка для PostgreSQL
    if "postgresql" in str(engine.url):
        with engine.connect() as conn:
            # Проверяем, какие таблицы созданы
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            logger.info(f"📊 Таблицы в PostgreSQL: {tables}")
            
except Exception as e:
    logger.info(f"❌ Ошибка при создании таблиц: {e}")
    import traceback
    traceback.print_exc()

logger.info("="*60 + "\n")

# Функция для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для проверки подключения (можно вызывать из других модулей)
def check_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.info(f"❌ Ошибка подключения к БД: {e}")
        return False