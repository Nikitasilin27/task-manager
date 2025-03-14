from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, engine
from models import Base
from crud import get_tasks, create_task, delete_task, update_task
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from fastapi import Body
from enum import StrEnum

# Pydantic-модель для входящих данных при создании задачи
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    reminder: bool = False
    completed: bool = False
    
class Priority(StrEnum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

# Pydantic-модель для вывода задачи
class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None  # Используем Optional для поддержки None
    deadline: Optional[datetime] = None
    priority: str
    reminder: bool
    completed: bool
    created_at: datetime

    class Config:
        orm_mode = True

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.on_event("startup")
async def startup():
    try:
        print("Starting application and creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)  # Удаляем старую таблицу
            await conn.run_sync(Base.metadata.create_all)  # Создаём новую с user_id
        print("Database tables created successfully.")
        async for session in get_db():
            tasks = await get_tasks(session, user_id=1)
            print(f"Found {len(tasks)} existing tasks.")
            if not tasks:
                print("Initializing default tasks...")
                await create_task(
                    session,
                    user_id=1,
                    title="Купить молоко",
                    deadline="2025-03-11T12:00:00",
                    priority="High",
                    reminder=True,
                    completed=False
                )
                await create_task(
                    session,
                    user_id=1,
                    title="Позвонить другу",
                    deadline="2025-03-12T14:00:00",
                    priority="Medium",
                    reminder=False,
                    completed=False
                )
                print("Default tasks created.")
    except Exception as e:
        print(f"Startup error: {str(e)}")

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
    except Exception as e:
        print(f"Error in create_task: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Ошибка при создании задачи: {str(e)}")

@app.delete("/tasks/{task_id}")
async def delete_task_endpoint(task_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    task = await delete_task(db, user_id=user_id, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена или не принадлежит пользователю")
    return {"message": "Задача удалена"}
    except Exception as e:
        print(f"Error in delete_task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None
    reminder: Optional[bool] = None
    completed: Optional[bool] = None

@app.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task_endpoint(task_id: int, task_update: TaskUpdate, user_id: int, db: AsyncSession = Depends(get_db)):
    task = await update_task(db, user_id=user_id, task_id=task_id, **task_update.dict(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена или не принадлежит пользователю")
    return task
