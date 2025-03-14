from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, engine
from models import Base
from crud import get_tasks, create_task, delete_task, update_task
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from enum import StrEnum
from contextlib import asynccontextmanager

# Pydantic-модель для входящих данных при создании задачи
class Priority(StrEnum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    reminder: bool = False
    completed: bool = False

# Pydantic-модель для вывода задачи
class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: str
    reminder: bool
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Pydantic-модель для обновления задачи
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None
    reminder: Optional[bool] = None
    completed: Optional[bool] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в Task Manager! Используйте /tasks для списка задач."}

@app.get("/tasks", response_model=list[TaskOut])
async def read_tasks(user_id: int, date: Optional[date] = None, db: AsyncSession = Depends(get_db)):
    tasks = await get_tasks(db, user_id=user_id, date=date)
    return tasks

@app.post("/tasks", response_model=TaskOut)
async def create_new_task(task: TaskCreate, user_id: int, db: AsyncSession = Depends(get_db)):
    new_task = await create_task(
        db,
        user_id=user_id,
        title=task.title,
        description=task.description,
        deadline=task.deadline,
        priority=task.priority,
        reminder=task.reminder,
        completed=task.completed
    )
    return new_task

@app.delete("/tasks/{task_id}")
async def delete_task_endpoint(task_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    task = await delete_task(db, user_id=user_id, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена или не принадлежит пользователю")
    return {"message": "Задача удалена"}

@app.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task_endpoint(task_id: int, task_update: TaskUpdate, user_id: int, db: AsyncSession = Depends(get_db)):
    task = await update_task(db, user_id=user_id, task_id=task_id, **task_update.dict(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена или не принадлежит пользователю")
    return task
