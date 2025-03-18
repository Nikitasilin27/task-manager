import asyncio
import logging
import sys
import os
from database import engine
from models import Base

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_db(drop_all=False):
    """
    Инициализирует базу данных, создавая или пересоздавая таблицы.
    
    Args:
        drop_all (bool): Если True, все существующие таблицы будут удалены перед созданием новых.
    """
    try:
        async with engine.begin() as conn:
            if drop_all:
                logger.warning("Сбрасываю все таблицы базы данных!")
                await conn.run_sync(Base.metadata.drop_all)
                logger.info("Все таблицы успешно удалены")
            
            # Создаем таблицы
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Таблицы базы данных успешно созданы с поддержкой временных зон")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {str(e)}")
        return False

if __name__ == "__main__":
    # Добавляем возможность указать опцию --drop для сброса БД
    drop_all = "--drop" in sys.argv
    
    # Предупреждение, если будет сбрасывать таблицы
    if drop_all:
        logger.warning("Вы собираетесь удалить все существующие таблицы. У вас есть 5 секунд, чтобы отменить операцию (Ctrl+C)")
        try:
            # Задержка для возможности отмены операции
            for i in range(5, 0, -1):
                print(f"Удаление через {i}...", end="\r")
                asyncio.run(asyncio.sleep(1))
        except KeyboardInterrupt:
            logger.info("Операция отменена пользователем")
            sys.exit(0)
    
    # Запускаем инициализацию БД
    success = asyncio.run(init_db(drop_all))
    
    # Выходим с соответствующим кодом
    sys.exit(0 if success else 1)
