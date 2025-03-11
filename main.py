from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, engine
from models import Base
from crud import get_tasks, create_task

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://task-manager-1-abs5.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Удаляем старые таблицы и создаём новые
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Удаляем старые таблицы
        await conn.run_sync(Base.metadata.create_all)  # Создаём новые таблицы
    # Добавляем тестовые задачи, если их нет
    async for session in get_db():
        tasks = await get_tasks(session)
        if not tasks:
            await create_task(session, title="Купить молоко", deadline="2025-03-11T12:00:00", priority="High", reminder=True, completed=False)
            await create_task(session, title="Позвонить другу", deadline="2025-03-12T14:00:00", priority="Medium", reminder=False, completed=False)
        break

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в Task Manager! Используйте /tasks для списка задач."}

@app.get("/tasks")
async def read_tasks(db: AsyncSession = Depends(get_db)):
    tasks = await get_tasks(db)
    return tasks

from pydantic import BaseModel
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    deadline: str | None = None
    priority: str = "Medium"
    reminder: bool = False
    completed: bool = False

@app.post("/tasks")
async def create_new_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_task = await create_task(
            db,
            title=task.title,
            description=task.description,
            deadline=task.deadline,
            priority=task.priority,
            reminder=task.reminder,
            completed=task.completed
        )
        return {"message": "Задача создана!", "task": new_task}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при создании задачи: {str(e)}")
