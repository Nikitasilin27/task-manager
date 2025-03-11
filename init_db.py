import asyncio
from database import engine
from models import Base

async def init_db():
    async with engine.begin() as conn:
        print("Модели, которые SQLAlchemy видит:", Base.metadata.tables.keys())
        await conn.run_sync(Base.metadata.drop_all)  # Удаляем таблицы для чистоты (опционально)
        await conn.run_sync(Base.metadata.create_all)
        print("Таблицы успешно созданы.")

if __name__ == "__main__":
    asyncio.run(init_db())
