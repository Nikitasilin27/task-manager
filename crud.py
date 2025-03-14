from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from models import Task
from datetime import datetime, date, timedelta, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_tasks(db: AsyncSession, user_id: int, date: Optional[date] = None):
    try:
        query = select(Task).where(Task.user_id == user_id)
        if date:
            # Используем func.date_trunc для обрезки времени до начала дня
            start_of_day = datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc)
            next_day = start_of_day + timedelta(days=1)
            query = query.where(
                and_(
                    func.date_trunc('day', Task.deadline) == start_of_day
                )
            )
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Ошибка при получении задач для user_id={user_id}: {str(e)}")
        raise

# Остальные функции (create_task, delete_task, update_task) остаются без изменений

async def create_task(db: AsyncSession, user_id: int, title: str, description: Optional[str] = None, 
                     deadline: Optional[str] = None, priority: str = "Medium", reminder: bool = False, 
                     completed: bool = False):
    logger.info(f"Создание задачи для user_id={user_id}, title={title}")
    try:
        existing_task = await db.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.title == title,
                Task.created_at >= datetime.utcnow() - timedelta(minutes=1)
            )
        )
        if existing_task.scalars().first():
            logger.info("Задача с таким названием уже существует, пропускаем создание.")
            return existing_task.scalars().first()

        deadline_dt = None
        if deadline:
            try:
                deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                if deadline_dt.tzinfo is None:
                    deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)
                else:
                    deadline_dt = deadline_dt.astimezone(timezone.utc)
            except ValueError as e:
                logger.error(f"Неверный формат deadline: {deadline}, ошибка: {str(e)}")
                raise ValueError(f"Неверный формат deadline: {deadline}")

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
        logger.info(f"Задача создана: id={db_task.id}, deadline в UTC: {db_task.deadline}")
        return db_task
    except Exception as e:
        logger.error(f"Ошибка при создании задачи для user_id={user_id}: {str(e)}")
        await db.rollback()
        raise

async def delete_task(db: AsyncSession, user_id: int, task_id: int):
    try:
        task = await db.get(Task, task_id)
        if not task or task.user_id != user_id:
            logger.warning(f"Задача с task_id={task_id} не найдена или не принадлежит user_id={user_id}")
            return None
        await db.delete(task)
        await db.commit()
        return task
    except Exception as e:
        logger.error(f"Ошибка при удалении задачи task_id={task_id}: {str(e)}")
        raise

async def update_task(db: AsyncSession, user_id: int, task_id: int, **kwargs):
    try:
        task = await db.get(Task, task_id)
        if not task or task.user_id != user_id:
            logger.warning(f"Задача с task_id={task_id} не найдена или не принадлежит user_id={user_id}")
            return None
        for key, value in kwargs.items():
            if value is not None:
                if key == "deadline" and value:
                    try:
                        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        if value.tzinfo is None:
                            value = value.replace(tzinfo=timezone.utc)
                        else:
                            value = value.astimezone(timezone.utc)
                    except ValueError as e:
                        logger.error(f"Неверный формат deadline в обновлении: {value}, ошибка: {str(e)}")
                        raise ValueError(f"Неверный формат deadline: {value}")
                setattr(task, key, value)
        await db.commit()
        await db.refresh(task)
        return task
    except Exception as e:
        logger.error(f"Ошибка при обновлении задачи task_id={task_id}: {str(e)}")
        raise
