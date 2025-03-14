from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from models import Task
from datetime import datetime, date, timedelta

async def get_tasks(db: AsyncSession, user_id: int, date: Optional[date] = None):
    query = select(Task).where(Task.user_id == user_id)
    if date:
        lower_bound = datetime.combine(date, datetime.min.time())
        upper_bound = lower_bound + timedelta(days=1)
        query = query.where(
            and_(
                Task.deadline >= lower_bound,
                Task.deadline < upper_bound
            )
        )
    result = await db.execute(query)
    return result.scalars().all()

async def create_task(db: AsyncSession, user_id: int, title: str, description: Optional[str] = None, deadline: Optional[str] = None, priority: str = "Medium", reminder: bool = False, completed: bool = False):
    print(f"Создаём задачу для user_id={user_id}, title={title}")  # Для отладки
    # Проверяем, есть ли уже такая задача у пользователя
    existing_task = await db.execute(
        select(Task).where(
            Task.user_id == user_id,
            Task.title == title,
            Task.created_at >= datetime.utcnow() - timedelta(minutes=1)
        )
    )
    if existing_task.scalars().first():
        print("Задача с таким названием уже существует, пропускаем создание.")  # Для отладки
        return existing_task.scalars().first()

    # Преобразуем дедлайн в UTC
    deadline_dt = None
    if deadline:
        deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))  # Предполагаем, что фронтенд отправляет в ISO формате
        if deadline_dt.tzinfo is None:
            deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)  # Если нет таймзоны, добавляем UTC
        else:
            deadline_dt = deadline_dt.astimezone(timezone.utc)  # Преобразуем в UTC, если есть другая таймзона

    db_task = Task(
        title=title,
        description=description,
        deadline=deadline_dt,
        priority=priority,
        reminder=reminder,
        completed=completed,
        user_id=user_id
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    print(f"Задача создана: id={db_task.id}, дедлайн в UTC: {db_task.deadline}")  # Для отладки
    return db_task

async def delete_task(db: AsyncSession, user_id: int, task_id: int):
    task = await db.get(Task, task_id)
    if not task or task.user_id != user_id:
        return None
    await db.delete(task)
    await db.commit()
    return task


async def update_task(db: AsyncSession, user_id: int, task_id: int, **kwargs):
    task = await db.get(Task, task_id)
    if not task or task.user_id != user_id:
        return None
    for key, value in kwargs.items():
        if value is not None:
            if key == "deadline" and value:
                value = datetime.fromisoformat(value)
            setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task
