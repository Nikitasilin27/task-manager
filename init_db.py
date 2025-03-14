import asyncio
from database import engine
from models import Base

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Сбрасывает все таблицы
        await conn.run_sync(Base.metadata.create_all)  # Создаёт таблицы заново
    print("Таблицы базы данных успешно пересозданы с поддержкой временных зон.")

if __name__ == "__main__":
    asyncio.run(init_db())
