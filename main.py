from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db, engine
from models import Base
from crud import get_tasks, create_task, delete_task, update_task
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import StrEnum
from contextlib import asynccontextmanager
from reminders import start_scheduler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: str
    reminder: bool
    completed: bool
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[Priority] = None
    reminder: Optional[bool] = None
    completed: Optional[bool] = None

class HealthResponse(BaseModel):
    status: str
    database: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Таблицы базы данных успешно созданы")
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц базы данных: {str(e)}")
        raise
    
    scheduler = start_scheduler()  # Запускаем планировщик
    yield
    # Останавливаем планировщик при завершении работы приложения
    scheduler.shutdown()

app = FastAPI(
    title="Task Manager API",
    description="API для управления задачами пользователей",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    logger.info(f"Получен запрос: {request.method} {request.url}")
    response = await call_next(request)
    process_time = datetime.now() - start_time
    logger.info(f"Ответ: статус {response.status_code}, время обработки: {process_time.total_seconds():.3f}s")
    return response

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(select(1))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Ошибка проверки состояния: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка проверки состояния")

@app.get("/", tags=["General"])
async def root():
    return {"message": "Добро пожаловать в Task Manager! Используйте /tasks для списка задач."}

@app.get("/tasks", response_model=List[TaskOut], tags=["Tasks"])
async def read_tasks(
    user_id: int, 
    date: Optional[date] = None, 
    db: AsyncSession = Depends(get_db)
):
    try:
        tasks = await get_tasks(db, user_id=user_id, date=date)
        return tasks
    except Exception as e:
        logger.error(f"Ошибка в read_tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Не удалось получить задачи: {str(e)}")

@app.post("/tasks", response_model=TaskOut, tags=["Tasks"])
async def create_new_task(
    task: TaskCreate, 
    user_id: int, 
    db: AsyncSession = Depends(get_db)
):
    try:
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
    except ValueError as ve:
        logger.error(f"Ошибка валидации в create_new_task: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Ошибка в create_new_task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Не удалось создать задачу: {str(e)}")

@app.delete("/tasks/{task_id}", tags=["Tasks"])
async def delete_task_endpoint(
    task_id: int, 
    user_id: int, 
    db: AsyncSession = Depends(get_db)
):
    try:
        task = await delete_task(db, user_id=user_id, task_id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена или не принадлежит пользователю")
        return {"message": "Задача удалена", "id": task_id}
    except Exception as e:
        logger.error(f"Ошибка в delete_task_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Не удалось удалить задачу: {str(e)}")

@app.patch("/tasks/{task_id}", response_model=TaskOut, tags=["Tasks"])
async def update_task_endpoint(
    task_id: int, 
    task_update: TaskUpdate, 
    user_id: int, 
    db: AsyncSession = Depends(get_db)
):
    try:
        task = await update_task(
            db, 
            user_id=user_id, 
            task_id=task_id, 
            **task_update.model_dump(exclude_unset=True)
        )
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена или не принадлежит пользователю")
        return task
    except ValueError as ve:
        logger.error(f"Ошибка валидации в update_task_endpoint: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Ошибка в update_task_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Не удалось обновить задачу: {str(e)}")
