from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone
import logging
from crud import get_tasks
import os
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
bot = Bot(os.environ.get("7822793225:AAFug__PTGhCEmMkPBii0I75KbsNHBuGXd8"))

async def get_telegram_users():
    updates = await bot.get_updates(offset=-1, timeout=10)
    user_ids = {update.message.chat.id for update in updates if update.message}
    return list(user_ids)

async def check_reminders():
    logger.info("Проверка напоминаний...")
    users = await get_telegram_users()  # Динамически получаем пользователей из Telegram
    for user_id in users:
        tasks = await get_tasks(None, user_id)  # Предполагаем, что get_tasks работает без сессии для простоты
        for task in tasks:
            if task.reminder and task.deadline and not task.completed:
                deadline = task.deadline.astimezone(timezone.utc)
                now = datetime.now(timezone.utc)
                if (deadline - now).total_seconds() <= 3600:  # Напоминание за час
                    logger.info(f"Напоминание для задачи {task.title} (user_id={user_id})")
                    await bot.send_message(chat_id=user_id, text=f"Напоминание: {task.title} (дедлайн: {deadline})")

def start_scheduler():
    scheduler.add_job(check_reminders, 'interval', minutes=1)
    scheduler.start()
    logger.info("Планировщик напоминаний запущен")
