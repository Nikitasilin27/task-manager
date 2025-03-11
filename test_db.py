import asyncio
from database import async_session
from crud import create_task

async def test_db():
    try:
        async with async_session() as session:
            task = await create_task(
                session,
                title="Тестовая задача",
                description="Проверяем работу базы",
                deadline="2025-03-11T12:00:00",
                priority="Medium",
                reminder=False,
                completed=False
            )
            print(f"✅ Создана задача: ID={task.id}, Название={task.title}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
