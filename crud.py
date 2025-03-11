from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, delete
from models import Task
from datetime import datetime, date, timedelta

async def get_tasks(db: AsyncSession, date: str = None):
    query = select(Task)
    if date:
        filter_date = datetime.strptime(date, "%Y-%m-%d").date()
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

async def delete_task(db: AsyncSession, task_id: int):
    # Находим задачу по ID
    task = await db.get(Task, task_id)
    if not task:
        return None  # Если задачи нет, возвращаем None
    # Удаляем задачу
    await db.delete(task)
    await db.commit()
    return task
