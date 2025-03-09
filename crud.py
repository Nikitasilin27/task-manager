from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Task

async def get_tasks(db: AsyncSession):
    result = await db.execute(select(Task))
    return result.scalars().all()

async def get_task_by_id(db: AsyncSession, task_id: int):
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()

async def create_task(db: AsyncSession, title: str, description: str = None, deadline=None, priority: str = "Medium", reminder: bool = False):
    new_task = Task(title=title, description=description, deadline=deadline, priority=priority, reminder=reminder)
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task

async def delete_task(db: AsyncSession, task_id: int):
    task = await get_task_by_id(db, task_id)
    if task:
        await db.delete(task)
        await db.commit()
        return True
    return False