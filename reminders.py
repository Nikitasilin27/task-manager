import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import aiohttp
from models import Task
from database import async_session

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан в переменных окружения")

scheduler = AsyncIOScheduler()

async def send_telegram_message(chat_id: int, message: str):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                print(f"Ошибка отправки сообщения: {await response.text()}")

async def check_reminders():
    async with async_session() as db:
        now = datetime.utcnow()
        one_hour_later = now + timedelta(hours=1)
        query = select(Task).where(
            Task.reminder == True,
            Task.deadline >= now,
            Task.deadline <= one_hour_later
        )
        result = await db.execute(query)
        tasks = result.scalars().all()
        for task in tasks:
            message = f"Напоминание: задача '{task.title}' через час! Дедлайн: {task.deadline}"
            await send_telegram_message(chat_id=task.user_id, message=message)
            task.reminder = False  # Отключаем, чтобы не повторялось
            await db.commit()

def start_scheduler():
    scheduler.add_job(check_reminders, 'interval', minutes=1)  # Проверка каждую минуту
    scheduler.start()
