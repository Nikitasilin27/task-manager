from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, engine
from models import Base
from crud import get_tasks

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в Task Manager! Используйте /tasks для списка задач."}

@app.get("/tasks")
async def read_tasks(db: AsyncSession = Depends(get_db)):
    return await get_tasks(db)

@app.post("/tasks")
async def create_new_task(db: AsyncSession = Depends(get_db), title: str = "Новая задача", description: str = None, deadline: str = None, priority: str = "Medium", reminder: bool = False):
    task = await create_task(db, title=title, description=description, deadline=deadline, priority=priority, reminder=reminder)
    return {"message": "Задача создана!", "task_id": task.id}
