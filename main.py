from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, engine
from models import Base
from crud import get_tasks, create_task, delete_task
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from datetime import datetime

# Pydantic-модель для входящих данных при создания задачи
class TaskCreate(BaseModel):
    title: str
    description: str = None
    deadline: str = None  # Формат ISO, например, "2025-03-11T12:00:00"
    priority: str = "Medium"
    reminder: bool = False
    completed: bool = False

# Pydantic-модель для вывода задачи
class TaskOut(BaseModel):
    id: int
    title: str
    description: str = None
    deadline: datetime = None
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
    allow_origins=["https://task-manager-1-abs5.onrender.com", "http://localhost"],  # Указываем фронтенд
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)



@app.on_event("startup")
async def startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async for session in get_db():
            tasks = await get_tasks(session)
            if not tasks:
                await create_task(
                    session,
                    title="Купить молоко",
                    deadline="2025-03-11T12:00:00",
                    priority="High",
                    reminder=True,
                    completed=False
                )
                await create_task(
                    session,
                    title="Позвонить другу",
                    deadline="2025-03-12T14:00:00",
                    priority="Medium",
                    reminder=False,
                    completed=False
                )
    except Exception as e:
        print(f"Ошибка при старте: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в Task Manager! Используйте /tasks для списка задач."}

@app.get("/tasks", response_model=list[TaskOut])
async def read_tasks(date: str = None, db: AsyncSession = Depends(get_db)):
    try:
        tasks = await get_tasks(db, date=date)
        return jsonable_encoder(tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")

@app.post("/tasks", response_model=TaskOut)
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
        return jsonable_encoder(new_task)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при создании задачи: {str(e)}")

@app.delete("/tasks/{task_id}")
async def delete_task_endpoint(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await delete_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return {"message": "Задача удалена"}
