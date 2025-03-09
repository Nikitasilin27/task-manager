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

@app.get("/tasks")
async def read_tasks(db: AsyncSession = Depends(get_db)):
    return await get_tasks(db)
