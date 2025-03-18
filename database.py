from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
import logging
from contextlib import asynccontextmanager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение URL базы данных из переменных окружения с резервным значением для разработки
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Для локальной разработки можно использовать SQLite
    logger.warning("DATABASE_URL не задан в переменных окружения, использую значение по умолчанию для разработки")
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/taskmanager"

# Преобразование URL для совместимости с asyncpg (если необходимо)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    logger.info("DATABASE_URL изменён для совместимости с asyncpg")

logger.info(f"Используется тип базы данных: {DATABASE_URL.split('://')[0]}")

# Создание асинхронного движка
engine = create_async_engine(
    DATABASE_URL,
    echo=bool(os.environ.get("SQL_ECHO", "False").lower() == "true"),
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,  # Пересоздает соединения каждые 30 минут
)

# Создание фабрики сессий
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Функция для получения сессии БД
async def get_db():
    """
    Асинхронный генератор для получения сессии базы данных.
    
    Yields:
        AsyncSession: Сессия базы данных
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Контекстный менеджер для работы с базой данных вне зависимостей FastAPI
@asynccontextmanager
async def get_db_context():
    """
    Асинхронный контекстный менеджер для работы с базой данных вне FastAPI.
    
    Yields:
        AsyncSession: Сессия базы данных
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
