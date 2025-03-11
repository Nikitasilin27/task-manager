from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from models import Task
from datetime import datetime, date

async def get_tasks(db: AsyncSession, date: str = None):
    query = select(Task)
    if date:
        # Преобразуем строку даты (например, "2025-03-12") в объект date
        filter_date = datetime.strptime(date, "%Y-%m-%d").date()
        # Фильтруем задачи, где deadline соответствует указанной дате
        query = query.where(
            and_(
                Task.deadline >= filter_date,
                Task.deadline < filter_date + timedelta(days=1)
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
