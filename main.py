from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, engine
from models import Base
from crud import get_tasks, create_task  # Предполагаю, что эти функции определены в crud.py

app = FastAPI()

# Настройка CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://task-manager-1-abs5.onrender.com"],  # Укажи URL фронтенда
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем GET, POST и другие методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

# Инициализация базы данных и начальных данных при старте
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Добавляем начальные тестовые задачи
    async with get_db() as db:
        tasks = await get_tasks(db)
        if not tasks:  # Если задач нет, добавляем тестовые
            await create_task(db, title="Купить молоко", deadline="2025-03-11", priority="High", reminder=True)
            await create_task(db, title="Позвонить другу", deadline="2025-03-12", priority="Medium", reminder=False)

# Корневой эндпоинт
@app.get("/")
async def root():
    return {"message": "Добро пожаловать в Task Manager! Используйте /tasks для списка задач."}

# Получение списка задач
@app.get("/tasks")
async def read_tasks(db: AsyncSession = Depends(get_db)):
    tasks = await get_tasks(db)
    return tasks  # Возвращаем список задач в формате JSON

# Создание новой задачи
from pydantic import BaseModel
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    deadline: str | None = None
    priority: str = "Medium"
    reminder: bool = False

@app.post("/tasks")
async def create_new_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Преобразуем deadline в ISO формат, если он есть
        deadline = datetime.fromisoformat(task.deadline).isoformat() if task.deadline else None
        # Создаём задачу
        new_task = await create_task(db, 
                                  title=task.title, 
                                  description=task.description, 
                                  deadline=deadline, 
                                  priority=task.priority, 
                                  reminder=task.reminder)
        return {"message": "Задача создана!", "task": new_task}
    except Exception as e:
        return {"error": f"Ошибка при создании задачи: {str(e)}"}, 400
