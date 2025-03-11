from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from models import Task
from datetime import datetime, timedelta

async def get_tasks(db: AsyncSession, date: str = None):
    query = select(Task)
    if date:
        # Преобразуем переданную строку в объект date
        filter_date = datetime.strptime(date, "%Y-%m-%d").date()
        # Создаём нижнюю и верхнюю границу как объекты datetime
        lower_bound = datetime.combine(filter_date, datetime.min.time())
        upper_bound = lower_bound + timedelta(days=1)
        query = query.where(
            and_(
                Task.deadline >= lower_bound,
                Task.deadline < upper_bound
            )
        )
    result = await db.execute(query)
    return result.scalars().all()

async def create_task(db: AsyncSession, title: str, description: str = None, deadline: str = None, priority: str = "Medium", reminder: bool = False, completed: bool = False):
    deadline_dt = datetime.fromisoformat(deadline) if deadline else None
    db_task = Task(
        title=title,
        description=description,
        deadline=deadline_dt,
        priority=priority,
        reminder=reminder,
        completed=completed
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

async def delete_task(db: AsyncSession, task_id: int):
    task = await db.get(Task, task_id)
    if not task:
        return None
    await db.delete(task)
    await db.commit()
    return task
